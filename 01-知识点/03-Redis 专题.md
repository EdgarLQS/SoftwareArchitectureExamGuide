# Redis 专题复习指南

## 一、Redis 概述

### 1.1 Redis 简介

**Redis**（Remote Dictionary Server）是一个开源的、基于内存的键值存储系统，常用作数据库、缓存和消息中间件。

**核心特点：**
- **基于内存**：数据存储在内存中，读写速度极快（10 万 + QPS）
- **键值存储**：Key-Value 数据结构，Key 必须是字符串
- **数据类型丰富**：支持 String、List、Set、ZSet、Hash 等
- **持久化支持**：RDB 快照 + AOF 日志
- **高可用**：支持主从复制、哨兵模式、集群
- **单线程模型**：基于 IO 多路复用，避免上下文切换

### 1.2 Redis 应用场景

| 场景 | 数据类型 | 说明 |
|------|---------|------|
| **缓存** | 所有类型 | 热点数据缓存、会话管理 |
| **分布式锁** | String | SETNX 实现互斥锁 |
| **计数器** | String | 点赞数、访问量、秒杀库存 |
| **排行榜** | ZSet | 游戏排行榜、热搜榜 |
| **消息队列** | List/Stream | 异步任务、延迟队列 |
| **购物车** | Hash | 用户购物车数据 |
| **社交关系** | Set | 共同好友、关注列表 |
| **地理位置** | Geo | 附近的人、位置追踪 |

---

## 二、Redis 数据结构（必考）

### 2.1 五大基本数据类型

#### 2.1.1 String（字符串）

**特点：**
- 二进制安全，最大存储 512MB
- 支持自增自减操作

**常用命令：**
```bash
SET key value              # 设置值
GET key                    # 获取值
SETNX key value            # 分布式锁（不存在才设置）
SETEX key seconds value    # 设置值 + 过期时间
INCR key                   # 自增 1
INCRBY key increment       # 自增指定值
DECR key                   # 自减 1
MSET key1 value1 key2 value2  # 批量设置
MGET key1 key2             # 批量获取
```

**应用场景：**
- 缓存用户信息、商品信息
- 分布式锁（SETNX）
- 计数器（点赞、浏览、秒杀）

---

#### 2.1.2 List（列表）

**特点：**
- 双向链表实现
- 元素有序、可重复
- 支持两端推送和弹出

**常用命令：**
```bash
LPUSH key value1 value2    # 左侧插入
RPUSH key value1 value2    # 右侧插入
LPOP key                   # 左侧弹出
RPOP key                   # 右侧弹出
LRANGE key start end       # 获取范围元素
LLEN key                   # 获取列表长度
LINDEX key index           # 获取指定索引元素
```

**应用场景：**
- 消息队列（LPUSH + RPOP）
- 最新列表（最新文章、最新动态）
- 栈和队列实现

---

#### 2.1.3 Hash（哈希）

**特点：**
- 键值对集合，适合存储对象
- 字段可独立修改

**常用命令：**
```bash
HSET key field value       # 设置字段值
HGET key field             # 获取字段值
HMSET key field1 v1 field2 v2  # 批量设置
HMGET key field1 field2    # 批量获取
HGETALL key                # 获取所有字段
HDEL key field             # 删除字段
HLEN key                   # 获取字段数量
HINCRBY key field increment # 字段自增
```

**应用场景：**
- 购物车（用户 ID 为 key，商品 ID 为 field）
- 用户画像（用户 ID 为 key，标签为 field）
- 对象存储（比 String 更灵活）

---

#### 2.1.4 Set（集合）

**特点：**
- 无序集合，元素唯一
- 支持交集、并集、差集运算

**常用命令：**
```bash
SADD key member1 member2   # 添加元素
SREM key member            # 删除元素
SMEMBERS key               # 获取所有元素
SISMEMBER key member       # 判断元素是否存在
SCARD key                  # 获取元素数量
SINTER key1 key2           # 交集
SUNION key1 key2           # 并集
SDIFF key1 key2            # 差集
```

**应用场景：**
- 好友关系、关注列表
- 共同好友（交集）
- 可能认识的人（差集）
- 抽奖系统（随机抽取）

---

#### 2.1.5 ZSet（有序集合）

**特点：**
- 有序集合，元素唯一
- 每个元素关联一个分数（score）
- 按分数排序

**常用命令：**
```bash
ZADD key score member1 score2 member2  # 添加元素
ZREM key member            # 删除元素
ZRANGE key start end [WITHSCORES]  # 按分数升序获取
ZREVRANGE key start end    # 按分数降序获取
ZRANK key member           # 获取排名
ZCARD key                  # 获取元素数量
ZINCRBY key increment member # 分数自增
ZCOUNT key min max         # 统计分数范围内的元素
```

**应用场景：**
- 排行榜（游戏、销售、热搜）
- 优先级队列
- 延迟队列（时间戳为 score）

---

### 2.2 三大特殊数据类型

#### 2.2.1 HyperLogLog

**特点：**
- 基数统计（去重计数）
- 占用空间固定（12KB）
- 有误差（0.81%）

**常用命令：**
```bash
PFADD key element1 element2  # 添加元素
PFCOUNT key                  # 获取基数
PFMERGE destkey sourcekey    # 合并
```

**应用场景：**
- UV 统计（网站独立访客）
- 海量数据去重

---

#### 2.2.2 Bitmap（位图）

**特点：**
- 按位存储，极致节省空间
- 适合布尔值场景

**常用命令：**
```bash
SETBIT key offset value    # 设置位值
GETBIT key offset          # 获取位值
BITCOUNT key               # 统计 1 的数量
BITOP op destkey key1 key2 # 位运算
```

**应用场景：**
- 用户签到
- 状态标记（在线/离线）
- 布隆过滤器基础

---

#### 2.2.3 Geo（地理位置）

**特点：**
- 存储经纬度坐标
- 支持距离计算、附近搜索

**常用命令：**
```bash
GEOADD key longitude latitude member  # 添加位置
GEODIST key member1 member2           # 计算距离
GEORADIUS key x y radius              # 指定半径搜索
GEORADIUSBYMEMBER key member radius   # 某成员附近搜索
```

**应用场景：**
- 附近的人
- 网约车位置
- 物流追踪

---

## 三、Redis 持久化（必考）

### 3.1 RDB（Redis Database）

**原理：**
- 定时将内存数据快照保存到磁盘
- 文件：dump.rdb
- 触发方式：手动触发（SAVE/BGSAVE）或自动触发（配置）

**配置示例：**
```conf
save 900 1        # 900 秒内至少 1 个 key 变化
save 300 10       # 300 秒内至少 10 个 key 变化
save 60 10000     # 60 秒内至少 10000 个 key 变化
```

**优点：**
- 恢复速度快
- 文件紧凑，适合备份
- 不影响主进程（BGSAVE）

**缺点：**
- 可能丢失最后一次快照后的数据
- 大数据量时 fork 子进程耗时

---

### 3.2 AOF（Append Only File）

**原理：**
- 记录每次写操作命令
- 重启时重放命令恢复数据
- 支持三种同步策略

**同步策略：**
| 策略 | 配置 | 数据安全性 | 性能 |
|------|------|-----------|------|
| 每秒同步 | everysec | 丢失 1 秒数据 | 推荐 |
| 每次同步 | always | 不丢失 | 差 |
| 从不同步 | no | 丢失最多 | 最好 |

**配置示例：**
```conf
appendonly yes                    # 开启 AOF
appendfsync everysec              # 每秒同步
auto-aof-rewrite-percentage 100   # AOF 文件增长 100% 时重写
```

**优点：**
- 数据更安全（最多丢失 1 秒）
- 可读性强（命令文本）

**缺点：**
- 文件体积大
- 恢复速度慢于 RDB

---

### 3.3 混合持久化（Redis 4.0+）

**原理：**
- RDB + AOF 结合
- AOF 重写时，将当前内存以 RDB 格式写入 AOF 文件头部
- 后续增量数据以 AOF 格式追加

**优点：**
- 兼具 RDB 恢复快和 AOF 数据安全
- 重写效率高

---

### 3.4 持久化选型建议

| 场景 | 推荐方案 |
|------|---------|
| 缓存（可丢失） | 关闭持久化 |
| 一般业务 | RDB + AOF（everysec） |
| 高安全要求 | AOF（always） |
| 大数据量 | 混合持久化 |

---

## 四、Redis 高可用架构（必考）

### 4.1 主从复制

**特点：**
- 一主多从架构
- 主库写，从库读（读写分离）
- 从库故障可切换

**配置：**
```conf
# 从库配置
replicaof 127.0.0.1 6379    # 指定主库
```

**复制过程：**
1. 从库连接主库，发送 PSYNC 命令
2. 主库执行 BGSAVE 生成 RDB
3. 主库发送 RDB 给从库
4. 从库加载 RDB
5. 主库发送缓冲区的新命令
6. 从库执行命令，完成同步

---

### 4.2 哨兵模式（Sentinel）

**作用：**
- 监控主从节点状态
- 自动故障转移
- 配置中心（通知客户端新主库）

**架构：**
```
        Sentinel 集群（3 节点）
           /    |    \
          /     |     \
      Master -- Slave1 -- Slave2
```

**故障转移流程：**
1. 哨兵监控到主库下线
2. 哨兵之间确认（quorum）
3. 选举一个哨兵执行故障转移
4. 选择一个从库晋升为主库
5. 通知其他从库和新主库同步
6. 通知客户端

**配置：**
```conf
sentinel monitor mymaster 127.0.0.1 6379 2  # quorum=2
sentinel down-after-milliseconds mymaster 5000
sentinel failover-timeout mymaster 60000
```

---

### 4.3 集群模式（Cluster）

**特点：**
- 去中心化，多主节点
- 数据分片存储（16384 个 slot）
- 自动故障转移

**架构：**
```
  Master1(0-5460)    Master2(5461-10922)   Master3(10923-16383)
     /    \             /    \                /    \
  Slave1 Slave2    Slave3 Slave4        Slave5 Slave6
```

**数据分片：**
- 16384 个槽（slot）
- Key 通过 CRC16 计算槽号：`CRC16(key) % 16384`
- 每个主节点负责部分槽

**客户端访问：**
- 客户端连接任意节点
- 如果 Key 不在该节点，返回 MOVED 错误并重定向
- 智能客户端会缓存槽分布

---

### 4.4 高可用方案对比

| 方案 | 优点 | 缺点 | 适用场景 |
|------|------|------|---------|
| **主从** | 简单、读写分离 | 手动切换 | 小规模 |
| **哨兵** | 自动故障转移 | 主库写瓶颈 | 中等规模 |
| **集群** | 高并发、高可用 | 复杂 | 大规模 |

---

## 五、缓存应用场景（高频考点）

### 5.1 缓存模式

#### 5.1.1 Cache-Aside（旁路缓存）

**流程：**
```
读：先读缓存 → 命中返回 → 未命中读数据库 → 写入缓存 → 返回
写：先写数据库 → 删除缓存
```

**代码示例：**
```java
// 读
String value = redis.get(key);
if (value == null) {
    value = db.query(key);
    redis.set(key, value);
}
return value;

// 写
db.update(key, value);
redis.del(key);  // 删除而非更新，避免并发问题
```

**优点：**
- 简单易懂
- 删除缓存比更新缓存更安全

**缺点：**
- 写操作后缓存未命中，影响性能

**适用：** 读多写少的场景

---

#### 5.1.2 Read/Write Through（穿透缓存）

**流程：**
```
读/写：操作缓存 → 缓存自动同步数据库
```

**特点：**
- 缓存和数据库整合为一个整体
- 由缓存层负责数据同步
- Redis 本身不支持，需要二次封装

---

#### 5.1.3 Write Behind（异步缓存写入）

**流程：**
```
写：只写缓存 → 异步批量写数据库
读：读缓存 → 未命中读数据库
```

**特点：**
- 写性能极高
- 可能丢失数据（缓存宕机）

**适用：** 高吞吐、可容忍丢失的场景

---

### 5.2 缓存三大问题（必考）

#### 5.2.1 缓存穿透

**问题描述：**
- 查询不存在的数据
- 缓存不命中，请求打到数据库
- 恶意攻击导致数据库压力大

**解决方案：**
1. **布隆过滤器**：快速判断 Key 是否存在
2. **缓存空对象**：即使不存在也缓存 null 值（设置短 TTL）
3. **接口限流**：限制同一 IP 的请求频率

**代码示例（缓存空值）：**
```java
String value = redis.get(key);
if ("NULL".equals(value)) {
    return null;  // 直接返回
}
if (value == null) {
    value = db.query(key);
    if (value == null) {
        redis.setex(key, 300, "NULL");  // 缓存空值 5 分钟
    } else {
        redis.set(key, value);
    }
}
```

---

#### 5.2.2 缓存击穿

**问题描述：**
- 热点 Key 突然过期
- 大量并发请求同时打到数据库
- 数据库瞬间压力大

**解决方案：**
1. **互斥锁**：只让一个线程查数据库，其他等待
2. **永不过期**：热点数据不设置 TTL
3. **提前预热**：过期前主动刷新

**代码示例（互斥锁）：**
```java
String value = redis.get(key);
if (value == null) {
    // 获取分布式锁
    if (redis.setnx(lockKey, "1") == 1) {
        try {
            // 双重检查
            value = redis.get(key);
            if (value == null) {
                value = db.query(key);
                redis.set(key, value);
            }
        } finally {
            redis.del(lockKey);
        }
    } else {
        // 等待后重试
        Thread.sleep(50);
        return query(key);
    }
}
```

---

#### 5.2.3 缓存雪崩

**问题描述：**
- 大量 Key 同时过期
- 或缓存服务宕机
- 请求全部打到数据库

**解决方案：**
1. **随机 TTL**：过期时间增加随机值
2. **高可用架构**：哨兵/集群
3. **限流降级**：数据库层限流
4. **多级缓存**：本地缓存 + Redis

**代码示例（随机 TTL）：**
```java
// 基础时间 + 随机时间（±10%）
int ttl = 3600 + new Random().nextInt(720);
redis.setex(key, ttl, value);
```

---

### 5.3 缓存一致性

**问题：**
- 数据库和缓存数据不一致

**解决方案：**

| 方案 | 做法 | 适用场景 |
|------|------|---------|
| **延时双删** | 写 DB → 删缓存 → 等待→再删缓存 | 强一致 |
| **监听 Binlog** | 监听 MySQL Binlog 异步删缓存 | 最终一致 |
| **先删缓存再写 DB** | 删缓存 → 写 DB → 读旧数据线程检测 | 最终一致 |

**推荐方案：Cache-Aside + 删除缓存**
- 写操作：先写数据库，再删除缓存
- 读操作：先读缓存，未命中读数据库并回写

---

## 六、分布式锁（高频考点）

### 6.1 实现原理

**核心命令：**
```bash
SETNX lock_key unique_value    # 互斥
EXPIRE lock_key 30             # 超时释放
```

**合并命令（原子性）：**
```bash
SET lock_key unique_value NX PX 30000
```

---

### 6.2 正确实现

**要求：**
1. 互斥性：同一时刻只有一个客户端持有锁
2. 防死锁：设置超时时间
3. 防误删：只能删除自己的锁
4. 原子性：使用 Lua 脚本

**代码示例：**
```java
// 加锁
String value = UUID.randomUUID().toString();
if (redis.set(lockKey, value, "NX", "PX", 30000) == true) {
    try {
        // 执行临界区代码
    } finally {
        // 解锁（Lua 脚本保证原子性）
        String lua = "if redis.call('get', KEYS[1]) == ARGV[1] then return redis.call('del', KEYS[1]) else return 0 end";
        redis.eval(lua, Collections.singletonList(lockKey), Collections.singletonList(value));
    }
}
```

---

### 6.3 RedLock（Redis 分布式锁）

**场景：**
- Redis 集群环境
- 单点故障可能导致锁失效

**算法步骤：**
1. 客户端获取当前时间 T1
2. 依次向 N 个 Redis 节点申请锁
3. 获取锁成功数量 >= N/2 + 1
4. 计算获取锁耗时 T2 - T1 < 锁有效期
5. 锁成功，否则释放所有锁

---

## 七、Redis 性能优化

### 7.1 内存优化

| 方法 | 说明 |
|------|------|
| 使用 Hash 代替 String | 对象字段多时用 Hash |
| 整数编码 | 小整数 Redis 自动优化 |
| 压缩列表 | 元素少时用 ziplist |
| 设置过期时间 | 定期清理无用数据 |
| 内存淘汰策略 | volatile-lru、allkeys-lru 等 |

---

### 7.2 大 Key 问题

**定义：**
- String > 10KB
- Hash/List/Set/ZSet > 1 万元素

**危害：**
- 网络阻塞
- 内存不均
- 删除时阻塞主线程

**解决方案：**
1. 拆分大 Key（Hash 分片）
2. 渐进式删除（UNLINK 代替 DEL）
3. 定期扫描大 Key

---

### 7.3 热 Key 问题

**定义：**
- 访问频率远超其他 Key

**危害：**
- 单节点压力大
- 可能触发限流

**解决方案：**
1. 本地缓存（Guava/Caffeine）
2. 热 Key 复制（多份副本）
3. 读写分离

---

### 7.4 慢查询优化

**命令：**
```bash
SLOWLOG GET 10       # 获取慢查询记录
SLOWLOG LEN          # 慢查询数量
CONFIG SET slowlog-log-slower-than 10000  # 设置阈值（微秒）
```

**优化建议：**
1. 避免 O(N) 命令（HGETALL、KEYS）
2. 批量操作使用 Pipeline
3. 禁用危险命令（KEYS、FLUSHALL）
4. 使用 MONITOR 分析慢命令

---

## 八、考点总结

### 8.1 案例分析考点

| 考点 | 考查形式 | 复习重点 |
|------|---------|---------|
| 缓存架构设计 | 设计题 | Cache-Aside 模式、三大问题 |
| 分布式锁 | 设计题 | SETNX、RedLock |
| 数据结构选型 | 选择/设计 | 五大类型特点和应用 |
| 高可用架构 | 设计题 | 主从、哨兵、集群对比 |
| 持久化方案 | 选择 | RDB vs AOF |

---

### 8.2 论文考点

**可能的论文主题：**
1. 缓存架构设计及应用
2. 分布式锁的实现与应用
3. 高并发系统的设计与实现
4. Redis 在 XX 系统中的应用

**论文素材准备：**
- 项目背景：电商/金融/社交系统
- 技术栈：Spring Boot + Redis + MySQL
- 解决的问题：性能瓶颈、高并发
- 效果：QPS 提升 XX%、响应时间降低 XX%

---

### 8.3 必背知识点

1. **五大数据类型及应用场景**
2. **RDB vs AOF 对比**
3. **主从/哨兵/集群对比**
4. **缓存三大问题及解决方案**
5. **分布式锁实现原理**
6. **缓存一致性方案**

---

## 九、典型例题

### 例题 1：缓存选型

**场景：** 设计一个电商系统，需要实现商品详情、购物车、商品排行榜功能。

**答案：**
```
1. 商品详情：String 或 Hash
   - Key: product:{id}
   - Value: 商品 JSON 数据

2. 购物车：Hash
   - Key: cart:{userId}
   - Field: productId
   - Value: 数量

3. 商品排行榜：ZSet
   - Key: product:rank:sales
   - Member: productId
   - Score: 销量
```

---

### 例题 2：缓存一致性

**问题：** 如何保证数据库和缓存的一致性？

**答案：**
```
推荐方案：Cache-Aside + 删除缓存

读操作：
1. 先读缓存
2. 命中返回
3. 未命中读数据库
4. 写入缓存
5. 返回

写操作：
1. 先写数据库
2. 删除缓存（非更新）
3. 原因：删除比更新更安全，避免并发写导致的不一致

特殊情况：
- 强一致场景：延时双删
- 高并发场景：监听 Binlog 异步删除
```

---

### 例题 3：高并发秒杀设计

**问题：** 设计一个秒杀系统，如何应对高并发？

**答案要点：**
```
1. 前端：按钮置灰、验证码、限流
2. 网关层：限流、黑名单
3. 缓存层：
   - 库存预热到 Redis
   - 扣库存用 Lua 脚本（原子性）
   - 分布式锁防止超卖
4. 消息队列：
   - 秒杀成功后发消息
   - 异步创建订单
5. 数据库：
   - 乐观锁（version）
   - 分库分表
```

---

## 十、备考资料

### 优先级 1（必看）
- `系统架构设计师\6、备考整理资料\系统架构设计师速记 50 个高频知识点.pdf`
- 案例分析真题：数据库/缓存相关题目

### 优先级 2（推荐）
- `系统架构设计师\6、备考整理资料\其他\微服务架构评述.pdf`
- `系统架构设计师\7、模拟题\` 相关模拟题

### 优先级 3（选看）
- 扩展阅读：《Redis 设计与实现》
- 实战练习：安装 Redis，练习常用命令
