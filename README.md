# 基于CP-ABE和区块链技术的数据安全共享系统

本系统是一个基于密文策略属性基加密（CP-ABE）和区块链技术的数据安全共享平台，旨在解决数据共享过程中的隐私保护、访问控制和数据追溯问题。

## 系统架构

系统采用分层架构设计，主要包括：

1. **用户层**：提供用户界面和交互功能
2. **应用层**：处理业务逻辑和API请求
3. **中间件层**：实现CP-ABE加密、区块链交互和分布式存储
4. **区块链层**：提供数据注册和属性管理服务
5. **存储层**：基于IPFS的分布式存储系统

## 核心功能

- **基于属性的加密访问控制**：使用CP-ABE技术根据用户属性控制数据访问权限
- **数据安全共享**：数据加密后存储在IPFS上，密文和访问策略注册到区块链
- **属性管理**：支持属性颁发、验证和撤销
- **可追溯性**：所有数据访问行为都在区块链上记录，确保可追溯性
- **隐私保护**：数据在共享过程中始终保持加密状态，只有满足访问策略的用户才能解密

## 技术栈

- **后端框架**：FastAPI
- **密码学库**：Charm-Crypto (CP-ABE)
- **区块链**：Ethereum (通过Web3.py交互)
- **分布式存储**：IPFS
- **数据库**：PostgreSQL

## 快速开始

### 环境准备

确保您已安装：

- Docker 和 Docker Compose
- Python 3.9+

### 使用Docker运行

1. 进入项目目录：

```bash
cd secure-data-sharing
```

2. 创建.env文件（可复制.env.example）：

```bash
cp .env.example .env
```

3. 使用Docker Compose启动服务：

```bash
docker-compose -f docker/docker-compose.yml up -d
```

4. 访问API文档：http://localhost:8000/docs

### 手动安装

1. 安装依赖：

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # 在Windows上使用 venv\Scripts\activate

# 安装Python依赖
pip install -r requirements.txt
```

2. 安装并启动IPFS：
   
```bash
# 下载并安装IPFS：https://docs.ipfs.io/install/
# 初始化IPFS
ipfs init
# 启动IPFS守护进程
ipfs daemon
```

3. 安装并启动本地以太坊测试网络（Ganache）：

```bash
# 安装Ganache CLI
npm install -g ganache-cli
# 启动Ganache
ganache-cli --deterministic
```

4. 部署智能合约：

```bash
# 设置智能合约目录
cd core/blockchain/contracts
# 使用truffle部署(需要先安装truffle: npm install -g truffle)
truffle migrate --network development
```

5. 更新.env文件中的合约地址和区块链节点URL。

6. *启动应用：

```bash
python run.py
```

## 系统流程

### 数据发布流程

1. 数据拥有者设置访问策略（CP-ABE策略表达式）
2. 系统使用CP-ABE加密数据
3. 加密数据上传到IPFS获取CID
4. 数据元信息和IPFS CID注册到区块链
5. 返回数据ID给用户

### 数据访问流程

1. 用户请求访问特定数据
2. 系统从区块链获取数据元信息和IPFS CID
3. 从IPFS获取加密数据
4. 系统验证用户属性是否满足访问策略
5. 如果满足，使用用户的CP-ABE密钥解密数据
6. 在区块链上记录访问操作
7. 返回解密后的数据给用户

### 属性管理流程

1. 属性颁发者为用户颁发属性
2. 系统在区块链上注册属性信息
3. 根据用户属性生成CP-ABE用户密钥
4. 用户可使用属性访问满足条件的数据

## API文档

启动应用后，访问以下URL查看完整API文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 项目结构

```
secure-data-sharing/
├── app/                      # 应用层
│   ├── api/                  # API定义
│   ├── middleware/           # 中间件
│   └── static/               # 静态文件
├── core/                     # 核心业务逻辑
│   ├── crypto/               # 密码学模块
│   ├── blockchain/           # 区块链模块
│   ├── storage/              # 存储模块
│   └── services/             # 业务服务
├── db/                       # 数据库
├── docker/                   # Docker配置
├── tests/                    # 测试
└── utils/                    # 工具函数
```

## 许可证

[MIT License](LICENSE)