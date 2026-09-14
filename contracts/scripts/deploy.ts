import { ethers } from "hardhat";

async function main() {
  const EvidenceRegistry = await ethers.getContractFactory("EvidenceRegistry");
  const registry = await EvidenceRegistry.deploy();
  await registry.waitForDeployment();
  console.log("EvidenceRegistry deployed to:", await registry.getAddress());
}

main().catch((e) => { console.error(e); process.exitCode = 1; });
