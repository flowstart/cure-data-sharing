// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title AttributeAuthority
 * @dev 管理用户属性的智能合约
 */
contract AttributeAuthority {
    // 用户属性结构
    struct UserAttribute {
        string name;           // 属性名称
        string value;          // 属性值
        uint256 issuedAt;      // 颁发时间
        uint256 expiresAt;     // 过期时间
        address issuer;        // 颁发者
        bool isRevoked;        // 是否已撤销
    }
    
    // 角色常量
    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");
    bytes32 public constant ISSUER_ROLE = keccak256("ISSUER_ROLE");
    
    // 角色映射: role => address => bool
    mapping(bytes32 => mapping(address => bool)) public roles;
    
    // 用户属性映射: userAddress => attributeId => UserAttribute
    mapping(address => mapping(bytes32 => UserAttribute)) public userAttributes;
    
    // 用户属性ID列表: userAddress => attributeId[]
    mapping(address => bytes32[]) public userAttributeIds;
    
    // 属性颁发者映射: attributeId => issuer
    mapping(bytes32 => address) public attributeIssuers;
    
    // 事件
    event AttributeIssued(address indexed user, bytes32 indexed attributeId, string name, string value, uint256 expiresAt);
    event AttributeRevoked(address indexed user, bytes32 indexed attributeId, address indexed revoker);
    event AttributeUpdated(address indexed user, bytes32 indexed attributeId, string name, string value, uint256 expiresAt);
    event RoleGranted(address indexed account, bytes32 indexed role);
    event RoleRevoked(address indexed account, bytes32 indexed role);
    
    // 部署合约时设置合约创建者为管理员
    constructor() {
        roles[ADMIN_ROLE][msg.sender] = true;
        emit RoleGranted(msg.sender, ADMIN_ROLE);
    }
    
    // 修饰符: 只有特定角色可以调用
    modifier onlyRole(bytes32 role) {
        require(roles[role][msg.sender], "Caller does not have the required role");
        _;
    }
    
    /**
     * @dev 授予角色给账户
     * @param role 角色
     * @param account 账户地址
     */
    function grantRole(bytes32 role, address account) public onlyRole(ADMIN_ROLE) {
        roles[role][account] = true;
        emit RoleGranted(account, role);
    }
    
    /**
     * @dev 撤销账户的角色
     * @param role 角色
     * @param account 账户地址
     */
    function revokeRole(bytes32 role, address account) public onlyRole(ADMIN_ROLE) {
        roles[role][account] = false;
        emit RoleRevoked(account, role);
    }
    
    /**
     * @dev 检查账户是否具有角色
     * @param role 角色
     * @param account 账户地址
     * @return bool 是否具有角色
     */
    function hasRole(bytes32 role, address account) public view returns (bool) {
        return roles[role][account];
    }
    
    /**
     * @dev 颁发属性给用户
     * @param user 用户地址
     * @param name 属性名称
     * @param value 属性值
     * @param expirationDays 过期天数
     * @return attributeId 属性ID
     */
    function issueAttribute(
        address user,
        string memory name,
        string memory value,
        uint256 expirationDays
    ) public onlyRole(ISSUER_ROLE) returns (bytes32) {
        // 确保用户地址不为零
        require(user != address(0), "Invalid user address");
        
        // 计算过期时间戳
        uint256 expiresAt = 0;
        if (expirationDays > 0) {
            expiresAt = block.timestamp + (expirationDays * 1 days);
        }
        
        // 生成属性ID
        bytes32 attributeId = keccak256(abi.encodePacked(user, name, msg.sender, block.timestamp));
        
        // 创建用户属性
        UserAttribute memory newAttribute = UserAttribute({
            name: name,
            value: value,
            issuedAt: block.timestamp,
            expiresAt: expiresAt,
            issuer: msg.sender,
            isRevoked: false
        });
        
        // 存储属性
        userAttributes[user][attributeId] = newAttribute;
        userAttributeIds[user].push(attributeId);
        attributeIssuers[attributeId] = msg.sender;
        
        // 触发事件
        emit AttributeIssued(user, attributeId, name, value, expiresAt);
        
        return attributeId;
    }
    
    /**
     * @dev 撤销用户的属性
     * @param user 用户地址
     * @param attributeId 属性ID
     */
    function revokeAttribute(address user, bytes32 attributeId) public {
        UserAttribute storage attribute = userAttributes[user][attributeId];
        
        // 确保属性存在
        require(attribute.issuer != address(0), "Attribute does not exist");
        
        // 确保属性未被撤销
        require(!attribute.isRevoked, "Attribute already revoked");
        
        // 只有属性颁发者或管理员可以撤销属性
        require(
            attribute.issuer == msg.sender || roles[ADMIN_ROLE][msg.sender],
            "Only the issuer or admin can revoke attributes"
        );
        
        // 标记为已撤销
        attribute.isRevoked = true;
        
        // 触发事件
        emit AttributeRevoked(user, attributeId, msg.sender);
    }
    
    /**
     * @dev 更新用户的属性
     * @param user 用户地址
     * @param attributeId 属性ID
     * @param value 新的属性值
     * @param expirationDays 新的过期天数
     */
    function updateAttribute(
        address user,
        bytes32 attributeId,
        string memory value,
        uint256 expirationDays
    ) public {
        UserAttribute storage attribute = userAttributes[user][attributeId];
        
        // 确保属性存在
        require(attribute.issuer != address(0), "Attribute does not exist");
        
        // 确保属性未被撤销
        require(!attribute.isRevoked, "Attribute is revoked");
        
        // 只有属性颁发者可以更新属性
        require(attribute.issuer == msg.sender, "Only the issuer can update attributes");
        
        // 更新属性值
        attribute.value = value;
        
        // 更新过期时间
        if (expirationDays > 0) {
            attribute.expiresAt = block.timestamp + (expirationDays * 1 days);
        }
        
        // 触发事件
        emit AttributeUpdated(user, attributeId, attribute.name, value, attribute.expiresAt);
    }
    
    /**
     * @dev 验证用户的属性是否有效
     * @param user 用户地址
     * @param attributeId 属性ID
     * @return isValid 属性是否有效
     */
    function validateAttribute(address user, bytes32 attributeId) public view returns (bool) {
        UserAttribute memory attribute = userAttributes[user][attributeId];
        
        // 确保属性存在
        if (attribute.issuer == address(0)) {
            return false;
        }
        
        // 确保属性未被撤销
        if (attribute.isRevoked) {
            return false;
        }
        
        // 检查属性是否已过期
        if (attribute.expiresAt > 0 && attribute.expiresAt < block.timestamp) {
            return false;
        }
        
        return true;
    }
    
    /**
     * @dev 获取用户的属性
     * @param user 用户地址
     * @param attributeId 属性ID
     * @return name 属性名称
     * @return value 属性值
     * @return issuedAt 颁发时间
     * @return expiresAt 过期时间
     * @return issuer 颁发者
     * @return isRevoked 是否已撤销
     * @return isValid 是否有效
     */
    function getAttribute(address user, bytes32 attributeId) public view returns (
        string memory name,
        string memory value,
        uint256 issuedAt,
        uint256 expiresAt,
        address issuer,
        bool isRevoked,
        bool isValid
    ) {
        UserAttribute memory attribute = userAttributes[user][attributeId];
        
        // 确保属性存在
        require(attribute.issuer != address(0), "Attribute does not exist");
        
        bool valid = validateAttribute(user, attributeId);
        
        return (
            attribute.name,
            attribute.value,
            attribute.issuedAt,
            attribute.expiresAt,
            attribute.issuer,
            attribute.isRevoked,
            valid
        );
    }
    
    /**
     * @dev 获取用户的属性数量
     * @param user 用户地址
     * @return count 属性数量
     */
    function getUserAttributeCount(address user) public view returns (uint256) {
        return userAttributeIds[user].length;
    }
    
    /**
     * @dev 获取用户的属性ID
     * @param user 用户地址
     * @param index 索引
     * @return attributeId 属性ID
     */
    function getUserAttributeIdAt(address user, uint256 index) public view returns (bytes32) {
        require(index < userAttributeIds[user].length, "Index out of range");
        return userAttributeIds[user][index];
    }
    
    /**
     * @dev 获取用户所有的属性ID
     * @param user 用户地址
     * @return attributeIds 属性ID数组
     */
    function getUserAttributeIds(address user) public view returns (bytes32[] memory) {
        return userAttributeIds[user];
    }
    
    /**
     * @dev 检查用户是否拥有特定名称和值的属性
     * @param user 用户地址
     * @param name 属性名称
     * @param value 属性值
     * @return hasAttribute 是否拥有属性
     */
    function hasAttribute(address user, string memory name, string memory value) public view returns (bool) {
        uint256 count = userAttributeIds[user].length;
        
        for (uint256 i = 0; i < count; i++) {
            bytes32 attributeId = userAttributeIds[user][i];
            UserAttribute memory attribute = userAttributes[user][attributeId];
            
            if (!attribute.isRevoked && (attribute.expiresAt == 0 || attribute.expiresAt > block.timestamp)) {
                if (keccak256(bytes(attribute.name)) == keccak256(bytes(name)) &&
                    keccak256(bytes(attribute.value)) == keccak256(bytes(value))) {
                    return true;
                }
            }
        }
        
        return false;
    }
    
    /**
     * @dev 批量验证用户的多个属性
     * @param user 用户地址
     * @param attributeIds 属性ID数组
     * @return validAttributes 有效属性的布尔数组
     */
    function validateAttributes(address user, bytes32[] memory attributeIds) public view returns (bool[] memory) {
        bool[] memory results = new bool[](attributeIds.length);
        
        for (uint256 i = 0; i < attributeIds.length; i++) {
            results[i] = validateAttribute(user, attributeIds[i]);
        }
        
        return results;
    }
    
    /**
     * @dev 根据属性名称获取用户的属性ID
     * @param user 用户地址
     * @param name 属性名称
     * @return attributeIds 属性ID数组
     */
    function getAttributeIdsByName(address user, string memory name) public view returns (bytes32[] memory) {
        uint256 count = userAttributeIds[user].length;
        
        // 计算匹配的属性数量
        uint256 matchCount = 0;
        for (uint256 i = 0; i < count; i++) {
            bytes32 attributeId = userAttributeIds[user][i];
            UserAttribute memory attribute = userAttributes[user][attributeId];
            
            if (keccak256(bytes(attribute.name)) == keccak256(bytes(name))) {
                matchCount++;
            }
        }
        
        // 创建结果数组
        bytes32[] memory result = new bytes32[](matchCount);
        uint256 resultIndex = 0;
        
        // 填充结果数组
        for (uint256 i = 0; i < count; i++) {
            bytes32 attributeId = userAttributeIds[user][i];
            UserAttribute memory attribute = userAttributes[user][attributeId];
            
            if (keccak256(bytes(attribute.name)) == keccak256(bytes(name))) {
                result[resultIndex] = attributeId;
                resultIndex++;
            }
        }
        
        return result;
    }
}