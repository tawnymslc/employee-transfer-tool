SCENARIOS = [
    {
        "id": "sandbox_credentials",
        "customer": "ABC Lending",
        "meeting_notes": (
            "Client was unable to make an API call. They were using production "
            "credentials instead of sandbox credentials. I guided them through "
            "logging into the sandbox environment, which uses a different URL, "
            "and generating a sandbox API key. They were then able to successfully "
            "make a GET Deal call. They need to review the returned deal data and "
            "let me know if any required information is missing. After reviewing "
            "the deal, they will POST an approval and let me know once it has been sent."
        ),
        "consultant_notes": (
            "Wait for the client to review the deal and send their approval."
        ),
        "expected": {
            "client_actions": [
                "Review returned deal data",
                "Report missing or incorrect deal data",
                "POST an approval",
                "Confirm when approval has been sent"
            ],
            "dependencies": [
                "Client review of deal data",
                "Client approval"
            ],
            "blocker": False
        }
    },

    {
        "id": "loan_configuration",
        "customer": "Summit Capital",
        "meeting_notes": (
            "Met with the lender team to review their loan configuration requirements. "
            "We discussed minimum annual revenue, maximum NSFs, supported states, "
            "minimum bankruptcy discharge period, credit score, and time in business. "
            "The lender still needs to confirm whether they have a maximum lien amount "
            "requirement and what minimum ownership percentage an applicant must have."
        ),
        "consultant_notes": (
            "Follow up for lien amount and ownership requirements."
        ),
        "expected": {
            "client_actions": [
                "Confirm maximum lien amount requirement",
                "Confirm minimum ownership percentage requirement"
            ],
            "dependencies": [
                "Outstanding loan configuration requirements"
            ],
            "blocker": False
        }
    },

    {
        "id": "live_deal_readiness",
        "customer": "Northstar Funding",
        "meeting_notes": (
            "Preparing the lender for pre-launch testing with five real borrowers. "
            "The lender needs to confirm internally that their team is ready before "
            "we open them to receive the borrowers. These are live deals but are still "
            "part of testing. The lender should review and underwrite each deal and "
            "send an Approval or DNQ. They should not communicate with the borrowers "
            "and should stop after sending the Approval or DNQ."
        ),
        "consultant_notes": (
            "Do not open the lender for the five borrowers until they confirm readiness."
        ),
        "expected": {
            "client_actions": [
                "Confirm internal readiness for live-deal testing",
                "Review and underwrite the five borrowers",
                "Send an Approval or DNQ"
            ],
            "dependencies": [
                "Lender readiness confirmation"
            ],
            "constraints": [
                "Do not communicate with borrowers",
                "Do not proceed beyond Approval or DNQ during testing"
            ],
            "blocker": False
        }
    },
    {
        "id": "contracts_out_failure",
        "customer": "Evergreen Capital",
        "meeting_notes": (
            "Met with the lender's technical team to test the API integration workflow. "
            "I sent a test deal and the lender confirmed they received the New Deal webhook. "
            "They successfully sent an approval using the API. I then acted as the borrower "
            "and accepted the offer, which triggered the Borrower Accepted webhook. The lender "
            "confirmed they received that webhook and moved on to sending a contract and "
            "updating the deal status to ContractsOut using the API. We reached the end of "
            "the workflow, but the ContractsOut status was not updated successfully. The lender "
            "needs to review the issue with their technical team and let me know when they are "
            "ready to test again."
        ),
        "consultant_notes": (
            "Wait for the lender's technical team to investigate the ContractsOut issue. "
            "Once they confirm they are ready to retest, send them a new test Deal ID."
        ),
        "expected": {
            "technical_issues": [
                "ContractsOut status was not updated successfully"
            ],
            "client_actions": [
                "Investigate the ContractsOut status issue",
                "Confirm when ready to retest"
            ],
            "internal_actions": [
                "Send a new test Deal ID when the lender is ready to retest"
            ],
            "dependencies": [
                "Lender technical investigation",
                "Lender readiness to retest"
            ],
            "blocker": False
        }
    },

    {
        "id": "approval_integration_blocker",
        "customer": "Pioneer Funding",
        "meeting_notes": (
            "The lender is successfully receiving new deals through the integration, but "
            "their system is not sending an approval after receiving the deal. Their technical "
            "team investigated the issue and determined that their integration code needs to "
            "be updated before an approval can be generated and sent back through the API. "
            "The approval workflow cannot be completed until their code changes are finished."
        ),
        "consultant_notes": (
            "Lender engineering owns the code changes. Wait for confirmation that the update "
            "has been deployed before scheduling another end-to-end API test."
        ),
        "expected": {
            "technical_issues": [
                "Lender integration is not sending an approval"
            ],
            "client_actions": [
                "Update lender integration code",
                "Confirm when the code changes are deployed"
            ],
            "dependencies": [
                "Lender code changes must be completed before end-to-end testing can continue"
            ],
            "blocker": True,
            "blocker_reason": (
                "The lender requires engineering changes to their integration code before "
                "the approval workflow can function."
            )
        }
    },

    {
        "id": "position_pricing_blocker",
        "customer": "Atlas Funding",
        "meeting_notes": (
            "Reviewed five live borrower deals with the lender after pre-launch testing. "
            "Lendio's configured pricing generated a $100,000 approval for one borrower, "
            "but after reviewing the borrower the lender determined they were only eligible "
            "for $50,000. We identified that the lender considers the position of the loan "
            "when determining pricing. A borrower in position two may receive a lower approval "
            "than a borrower in position one. Lendio's current pricing configuration only "
            "supports the position-one pricing rules and cannot configure different pricing "
            "based on loan position."
        ),
        "consultant_notes": (
            "Pricing generated by Lendio does not consistently match the lender's actual "
            "approval because we cannot configure their position-based pricing requirements. "
            "This needs internal review to determine how we can support the lender's pricing model."
        ),
        "expected": {
            "technical_issues": [
                "Lendio-generated pricing does not match lender pricing",
                "Lendio cannot configure pricing based on loan position"
            ],
            "internal_actions": [
                "Review the position-based pricing limitation internally",
                "Determine how the lender's pricing model can be supported"
            ],
            "dependencies": [
                "Resolution of the position-based pricing limitation"
            ],
            "blocker": True,
            "blocker_reason": (
                "The current Lendio product configuration cannot represent the lender's "
                "position-based pricing rules."
            )
        }
    },

    {
        "id": "implementation_kickoff",
        "customer": "Horizon Lending",
        "meeting_notes": (
            "Held the implementation kickoff with the lender team. We completed introductions, "
            "reviewed implementation expectations and the expected launch timeline, discussed "
            "their loan product at a high level, identified the primary contacts, and discussed "
            "weekly implementation calls. The next two meetings will be a Loan Configuration "
            "call with the lender's underwriting team to review their lending requirements and "
            "an API call with their technical team to review the integration workflow. Times "
            "were agreed on for both meetings."
        ),
        "consultant_notes": (
            "Send kickoff follow-up with the expected launch timeline, contact information, "
            "weekly call expectations, the scheduled Loan Configuration call, the scheduled "
            "API call, and next steps."
        ),
        "expected": {
            "internal_actions": [
                "Send kickoff follow-up email"
            ],
            "next_steps": [
                "Hold Loan Configuration call with underwriting team",
                "Hold API workflow call with technical team"
            ],
            "blocker": False
        }
    }
]