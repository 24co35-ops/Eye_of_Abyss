// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title EvidenceRegistry
 * @notice Tamper-proof on-chain anchor for Eye of Abyss forensic evidence packages.
 * Enforces owner/relayer authorization and emergency pause controls.
 */
contract EvidenceRegistry {
    // ── Access Control & State ───────────────────────────────────────────────
    address public owner;
    bool public paused;
    mapping(address => bool) public authorizedRelayers;

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

    // ── Events ───────────────────────────────────────────────────────────────
    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);
    event RelayerStatusUpdated(address indexed relayer, bool authorized);
    event Paused(address indexed account);
    event Unpaused(address indexed account);
    event EvidenceAnchored(
        bytes32 indexed evidenceHash,
        string caseId,
        string moduleId,
        address indexed submittedBy,
        uint256 timestamp
    );

    // ── Modifiers ─────────────────────────────────────────────────────────────
    modifier onlyOwner() {
        require(msg.sender == owner, "EvidenceRegistry: caller is not the owner");
        _;
    }

    modifier onlyAuthorized() {
        require(msg.sender == owner || authorizedRelayers[msg.sender], "EvidenceRegistry: caller not authorized to anchor");
        _;
    }

    modifier whenNotPaused() {
        require(!paused, "EvidenceRegistry: contract is paused");
        _;
    }

    // ── Constructor ───────────────────────────────────────────────────────────
    constructor() {
        owner = msg.sender;
        authorizedRelayers[msg.sender] = true;
        emit OwnershipTransferred(address(0), msg.sender);
        emit RelayerStatusUpdated(msg.sender, true);
    }

    // ── Management Functions ──────────────────────────────────────────────────
    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "EvidenceRegistry: new owner is zero address");
        emit OwnershipTransferred(owner, newOwner);
        owner = newOwner;
    }

    function setRelayer(address relayer, bool authorized) external onlyOwner {
        require(relayer != address(0), "EvidenceRegistry: invalid relayer address");
        authorizedRelayers[relayer] = authorized;
        emit RelayerStatusUpdated(relayer, authorized);
    }

    function pause() external onlyOwner {
        require(!paused, "EvidenceRegistry: already paused");
        paused = true;
        emit Paused(msg.sender);
    }

    function unpause() external onlyOwner {
        require(paused, "EvidenceRegistry: not paused");
        paused = false;
        emit Unpaused(msg.sender);
    }

    // ── Anchoring ─────────────────────────────────────────────────────────────
    function anchor(
        bytes32 evidenceHash,
        string memory caseId,
        string memory moduleId,
        string memory ipfsCid
    ) external onlyAuthorized whenNotPaused {
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

        emit EvidenceAnchored(evidenceHash, caseId, moduleId, msg.sender, block.timestamp);
    }

    function verify(bytes32 evidenceHash) external view returns (bool, uint256) {
        EvidenceRecord memory r = records[evidenceHash];
        return (r.timestamp > 0, r.timestamp);
    }
}
