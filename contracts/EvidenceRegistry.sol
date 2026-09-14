// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract EvidenceRegistry {
    struct EvidenceRecord {
        bytes32 evidenceHash;    // SHA-256 of evidence object
        uint256 timestamp;
        address submittedBy;
        string caseId;           // UUID string
        string moduleId;
        string ipfsCid;
    }

    mapping(bytes32 => EvidenceRecord) public records;
    mapping(string => bytes32[]) public caseEvidence; // caseId => evidence hashes

    event EvidenceAnchored(
        bytes32 indexed evidenceHash,
        string caseId,
        string moduleId,
        uint256 timestamp
    );

    function anchor(
        bytes32 evidenceHash,
        string memory caseId,
        string memory moduleId,
        string memory ipfsCid
    ) external {
        require(records[evidenceHash].timestamp == 0, "Already anchored");

        records[evidenceHash] = EvidenceRecord({
            evidenceHash: evidenceHash,
            timestamp: block.timestamp,
            submittedBy: msg.sender,
            caseId: caseId,
            moduleId: moduleId,
            ipfsCid: ipfsCid
        });

        caseEvidence[caseId].push(evidenceHash);

        emit EvidenceAnchored(evidenceHash, caseId, moduleId, block.timestamp);
    }

    function verify(bytes32 evidenceHash) external view returns (bool, uint256) {
        EvidenceRecord memory r = records[evidenceHash];
        return (r.timestamp > 0, r.timestamp);
    }
}
