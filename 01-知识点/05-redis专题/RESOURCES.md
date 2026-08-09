# Redis 专题 Resources

## Knowledge

- [Redis 官方：数据类型](https://redis.io/docs/latest/develop/data-types/)
  用于核对 String、List、Hash、Set、Sorted Set、Bitmap、Stream、概率型结构等数据模型和适用场景。
- [Redis 官方：持久化](https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/)
  用于核对 RDB、AOF、混合持久化、恢复速度和数据丢失窗口。
- [Redis 官方：复制](https://redis.io/docs/latest/operate/oss_and_stack/management/replication/)
  用于核对异步复制、PSYNC、部分重同步、复制偏移量和主从故障边界。
- [Redis 官方：Sentinel](https://redis.io/docs/latest/operate/oss_and_stack/management/sentinel/)
  用于核对监控、故障转移、quorum 和 Sentinel 的一致性边界。
- [Redis 官方：Cluster 规范](https://redis.io/docs/latest/operate/oss_and_stack/reference/cluster-spec/)
  用于核对槽位分片、节点故障和 Cluster 的异步复制特征。
- [系统架构设计师备考计划](../../2026下半年系统架构设计师备考计划.md)
  用于确定综合知识、案例分析、论文三科的训练节奏和 D0/D+2/D+7/D+21 回归方式。
- [历年案例薄弱点汇总](../../03-案例专题/000-历年真题/薄弱点汇总-2019-2025.md)
  用于确认 Redis/缓存考点出现的题型、年份和资料完整性；图片占位或缺题内容不作为完整原始试题。
- [Redis 完整参考库](./01-Redis专题复习指南.md)
  本仓库已有的 Redis 整理稿；后续新增内容应补充、纠错或链接到这里，不再复制同一套知识点。

## Wisdom

当前以官方文档、仓库内真题和实验结果为主，暂不把社区帖子作为考试结论来源。遇到版本差异时，先记录 Redis 版本、官方链接和验证日期，再更新专题内容。

## Gaps

- 2026 年考试大纲和所在地考试安排需要在正式报名或考试前再次核对官方公告。
- 本专题暂未完成真实 Redis 服务上的复制、Sentinel 和 Cluster 故障演练；文档中的实验步骤在执行前均标记为“未执行”。
