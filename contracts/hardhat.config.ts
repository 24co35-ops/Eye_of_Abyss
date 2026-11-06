import { HardhatUserConfig } from "hardhat/config";
import "@nomicfoundation/hardhat-toolbox";
import * as dotenv from "dotenv";
dotenv.config({ path: "../.env" });

const rawKey = (process.env.PRIVATE_KEY || "").trim();
const validKey = (rawKey.startsWith("0x") && rawKey.length === 66)
  ? [rawKey]
  : (rawKey.length === 64 && !rawKey.startsWith("0x") ? [`0x${rawKey}`] : []);

const config: HardhatUserConfig = {
  solidity: "0.8.20",
  networks: {
    polygonMumbai: {
      url: process.env.POLYGON_RPC_URL || "https://rpc-mumbai.maticvigil.com",
      accounts: validKey,
    },
    polygonAmoy: {
      url: process.env.POLYGON_AMOY_RPC_URL || "https://rpc-amoy.polygon.technology",
      accounts: validKey,
    },
  },
  etherscan: {
    apiKey: process.env.ETHERSCAN_API_KEY || process.env.POLYGONSCAN_API_KEY || "",
  },
};

export default config;
