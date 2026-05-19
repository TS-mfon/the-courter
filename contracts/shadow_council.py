# { "Depends": "py-genlayer:test" }

from dataclasses import dataclass
from genlayer import *


@allow_storage
@dataclass
class CouncilMember:
    voting_weight: u256
    active: bool


class ShadowCouncil(gl.Contract):
    owner: Address
    members: TreeMap[Address, CouncilMember]
    votes: TreeMap[str, TreeMap[Address, str]]
    yes_weight: TreeMap[str, u256]
    no_weight: TreeMap[str, u256]

    def __init__(self):
        self.owner = gl.message.sender_address

    @gl.public.write
    def set_member(self, wallet: Address, voting_weight: u256, active: bool) -> None:
        if gl.message.sender_address != self.owner:
            raise gl.UserError("Only owner")
        self.members[wallet] = CouncilMember(voting_weight=voting_weight, active=active)

    @gl.public.write
    def vote(self, proposal_id: str, vote_value: str) -> str:
        sender = gl.message.sender_address
        member = self.members[sender]
        if not member.active:
            raise gl.UserError("Only active governance reviewers may vote")
        existing = self.votes[proposal_id][sender]
        if existing:
            raise gl.UserError("Wallet has already voted")

        vote_upper = vote_value.upper()
        if vote_upper != "YES" and vote_upper != "NO":
            raise gl.UserError("Vote must be YES or NO")

        self.votes[proposal_id][sender] = vote_upper
        if vote_upper == "YES":
            self.yes_weight[proposal_id] += member.voting_weight
        else:
            self.no_weight[proposal_id] += member.voting_weight
        return "vote_recorded"

    @gl.public.view
    def result(self, proposal_id: str) -> str:
        if self.yes_weight[proposal_id] > self.no_weight[proposal_id]:
            return "upheld"
        return "overruled"
