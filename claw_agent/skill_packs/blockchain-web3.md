# Blockchain & Web3 Skill Pack

## Smart Contract Security
- **Reentrancy**: Checks-Effects-Interactions pattern. Use ReentrancyGuard
- **Integer Safety**: Solidity 0.8+ has built-in overflow checks. Use SafeMath for older versions
- **Access Control**: OpenZeppelin Ownable/AccessControl. Never trust tx.origin
- **Front-running**: Commit-reveal schemes. Use private mempools or Flashbots
- **Oracle Manipulation**: TWAP over spot price. Multiple oracle sources. Sanity bounds

## Solidity Patterns
- **Upgradeable**: Transparent proxy or UUPS pattern. Initialize not construct
- **Gas Optimization**: Pack storage variables. Use events not storage for read-rarely data
- **Error Handling**: Custom errors over require strings (cheaper gas)
- **Testing**: Foundry for fast Solidity tests. Hardhat for JS/TS integration tests
- **Auditing**: Slither for static analysis. Mythril for symbolic execution. Manual review always

## DeFi Patterns
- **AMM**: Constant product (x*y=k). Concentrated liquidity for capital efficiency
- **Lending**: Over-collateralized. Liquidation thresholds. Oracle-dependent pricing
- **Staking**: Reward distribution per share. Checkpoint-based accounting
- **Token Standards**: ERC-20, ERC-721, ERC-1155. Follow the standard exactly

## Ethereum Development
- **Keccak-256**: Node.js `sha3-256` is NOT Keccak. Use `keccak256` from ethers/viem
- **ABI Encoding**: ethers.js v6 or viem. Typed contracts with TypeChain or wagmi CLI
- **Decimal Handling**: Query `decimals()` on-chain. Never hardcode 18. Bridged tokens drift
- **Events**: Index important fields. Use events as the primary data source for off-chain indexing
