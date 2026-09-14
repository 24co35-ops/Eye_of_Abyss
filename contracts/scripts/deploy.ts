import { ethers, network } from "hardhat";

async function main() {
  const [deployer] = await ethers.getSigners();
  console.log(`Deploying EvidenceRegistry to network: ${network.name}`);
  console.log(`Deployer address: ${deployer ? deployer.address : "unknown"}`);

  const EvidenceRegistry = await ethers.getContractFactory("EvidenceRegistry");
  const registry = await EvidenceRegistry.deploy();
  await registry.waitForDeployment();

  const contractAddress = await registry.getAddress();
  console.log(`\n========================================`);
  console.log(`EvidenceRegistry deployed successfully!`);
  console.log(`Contract Address: ${contractAddress}`);
  console.log(`Network:          ${network.name}`);
  console.log(`========================================\n`);
  console.log(`Set the following in your .env file:`);
  console.log(`EVIDENCE_REGISTRY_ADDRESS=${contractAddress}`);
}

main().catch((e) => {
  console.error("Deployment failed:", e);
  process.exitCode = 1;
});

