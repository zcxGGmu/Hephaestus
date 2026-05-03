'use client';

import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Button } from '@/components/ui/button';
import {
  BarChart3,
  Briefcase,
  Settings,
  RefreshCw,
  TrendingUp,
  Users,
  Shield,
  Target,
  Brain,
  Globe,
  Heart,
  PenTool,
  Camera,
  Calendar,
  DollarSign,
  Rocket,
} from 'lucide-react';

type PromptExample = {
  title: string;
  query: string;
  icon: React.ReactNode;
};

const allPrompts: PromptExample[] = [
  {
    title: '寻找最佳面包店',
    query:
      '1. 在 {{city}} 搜索口碑最好的面包店\n2. 筛选出 {{number}} 家热门门店\n3. 整理评分、营业时间、地址和招牌产品\n4. 对比价格区间和特色\n5. 输出一份推荐清单',
    icon: <Globe className="text-blue-700 dark:text-blue-400" size={16} />,
  },
  {
    title: '研究教育数据',
    query:
      '1. 收集 {{topic}} 相关教育统计数据\n2. 汇总入学率、师生比和教育支出\n3. 整理成结构化表格\n4. 分析趋势与区域差异\n5. 输出执行摘要',
    icon: <BarChart3 className="text-purple-700 dark:text-purple-400" size={16} />,
  },
  {
    title: '计划旅行行程',
    query:
      '1. 为 {{destination}} 设计一份 {{duration}} 天行程\n2. 挑选景点、餐厅和体验活动\n3. 按地理位置优化每日路线\n4. 加入交通、天气和备选方案\n5. 输出逐日行程表',
    icon: <Calendar className="text-rose-700 dark:text-rose-400" size={16} />,
  },
  {
    title: '分析新闻报道',
    query:
      '1. 收集 {{news_outlet}} 在 {{time_period}} 内关于 {{topic}} 的报道\n2. 归纳主要观点和信息来源\n3. 建立关键事件时间线\n4. 标记分歧和信息空白\n5. 生成分析报告',
    icon: <PenTool className="text-indigo-700 dark:text-indigo-400" size={16} />,
  },
  {
    title: '构建财务模型',
    query:
      '1. 为 {{company_type}} 设计 {{model_type}} 财务模型\n2. 汇总历史数据和行业基准\n3. 预测收入、成本与现金流\n4. 补充关键指标分析\n5. 输出可复用的模型结构',
    icon: <DollarSign className="text-orange-700 dark:text-orange-400" size={16} />,
  },
  {
    title: '制定市场策略',
    query:
      '1. 为 {{product_type}} 制定市场进入策略\n2. 分析目标用户和竞争格局\n3. 规划定位、定价和渠道\n4. 制定上线节奏与预算框架\n5. 输出策略建议',
    icon: <Target className="text-cyan-700 dark:text-cyan-400" size={16} />,
  },
  {
    title: '研究公司情报',
    query:
      '1. 调研 {{company_name}} 的公开信息\n2. 收集融资、产品、客户和团队资料\n3. 分析竞争位置与增长方向\n4. 总结关键风险和机会\n5. 生成情报摘要',
    icon: <Briefcase className="text-teal-700 dark:text-teal-400" size={16} />,
  },
  {
    title: '审计日程生产力',
    query:
      '1. 分析过去 {{months}} 个月的日程安排\n2. 统计会议频率、专注时间和碎片时间\n3. 找出低效模式\n4. 提出优化建议\n5. 输出行动计划',
    icon: <Calendar className="text-violet-700 dark:text-violet-400" size={16} />,
  },
  {
    title: '研究行业趋势',
    query:
      '1. 研究 {{industry}} 的最新趋势\n2. 收集投融资、技术和市场动态\n3. 分析主要驱动因素\n4. 识别新机会与风险\n5. 输出趋势报告',
    icon: <TrendingUp className="text-pink-700 dark:text-pink-400" size={16} />,
  },
  {
    title: '自动化客服工单',
    query:
      '1. 汇总 {{support_platform}} 中的工单\n2. 按问题类型和紧急程度分类\n3. 匹配知识库中的解决方案\n4. 识别需要升级处理的事项\n5. 生成处理建议',
    icon: <Shield className="text-yellow-600 dark:text-yellow-300" size={16} />,
  },
  {
    title: '研究法律合规',
    query:
      '1. 梳理 {{jurisdictions}} 关于 {{legal_topic}} 的要求\n2. 对比适用范围、流程和成本\n3. 总结合规风险点\n4. 列出实施步骤\n5. 输出比较表',
    icon: <Settings className="text-red-700 dark:text-red-400" size={16} />,
  },
  {
    title: '编制数据分析',
    query:
      '1. 收集 {{data_topic}} 数据\n2. 清洗并标准化字段\n3. 计算关键指标和趋势\n4. 生成图表和摘要\n5. 提供结论建议',
    icon: <BarChart3 className="text-slate-700 dark:text-slate-400" size={16} />,
  },
  {
    title: '计划社交媒体内容',
    query:
      '1. 为 {{brand}} 制定 {{duration}} 的内容计划\n2. 分析热门话题和竞品内容\n3. 设计每周发布节奏\n4. 输出平台化文案方向\n5. 形成内容日历',
    icon: <Camera className="text-stone-700 dark:text-stone-400" size={16} />,
  },
  {
    title: '比较产品方案',
    query:
      '1. 对比 {{product_category}} 的主流方案\n2. 收集功能、优缺点和价格\n3. 分析适用场景\n4. 识别风险与限制\n5. 给出推荐意见',
    icon: <Brain className="text-fuchsia-700 dark:text-fuchsia-400" size={16} />,
  },
  {
    title: '分析市场机会',
    query:
      '1. 调研 {{market_topic}} 的市场机会\n2. 估算市场规模和增长空间\n3. 分析主要参与者和竞争壁垒\n4. 总结风险与进入门槛\n5. 输出机会评估',
    icon: <Rocket className="text-green-600 dark:text-green-300" size={16} />,
  },
  {
    title: '处理发票和文档',
    query:
      '1. 扫描 {{document_folder}} 中的 PDF 发票\n2. 提取编号、日期、金额和供应商\n3. 结构化整理字段\n4. 汇总成电子表格\n5. 生成财务摘要',
    icon: <Heart className="text-amber-700 dark:text-amber-400" size={16} />,
  },
  {
    title: '寻找人才候选人',
    query:
      '1. 在 {{location}} 搜索 {{job_title}} 候选人\n2. 汇总公开资料和技能信息\n3. 对比经验与岗位匹配度\n4. 形成候选人短名单\n5. 输出联系建议',
    icon: <Users className="text-blue-600 dark:text-blue-300" size={16} />,
  },
];

const getRandomPrompts = (count: number = 3): PromptExample[] => {
  const shuffled = [...allPrompts].sort(() => 0.5 - Math.random());
  return shuffled.slice(0, count);
};

export const Examples = ({
  onSelectPrompt,
  count = 3,
}: {
  onSelectPrompt?: (query: string) => void;
  count?: number;
}) => {
  const [displayedPrompts, setDisplayedPrompts] = useState<PromptExample[]>([]);
  const [isRefreshing, setIsRefreshing] = useState(false);

  useEffect(() => {
    setDisplayedPrompts(getRandomPrompts(count));
  }, [count]);

  const handleRefresh = () => {
    setIsRefreshing(true);
    setDisplayedPrompts(getRandomPrompts(count));
    setTimeout(() => setIsRefreshing(false), 300);
  };

  return (
    <div className="w-full max-w-4xl mx-auto px-4">
      <div className="group relative">
        <div className="flex gap-2 justify-center py-2 flex-wrap">
          {displayedPrompts.map((prompt, index) => (
            <motion.div
              key={`${prompt.title}-${index}`}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{
                duration: 0.3,
                delay: index * 0.03,
                ease: 'easeOut',
              }}
            >
              <Button
                variant="outline"
                className="w-fit h-fit px-3 py-2 rounded-full border-neutral-200 dark:border-neutral-800 bg-neutral-50 hover:bg-neutral-100 dark:bg-neutral-900 dark:hover:bg-neutral-800 text-sm font-normal text-muted-foreground hover:text-foreground transition-colors"
                onClick={() => onSelectPrompt && onSelectPrompt(prompt.query)}
              >
                <div className="flex items-center gap-2">
                  <div className="flex-shrink-0">
                    {React.cloneElement(prompt.icon as React.ReactElement, {
                      size: 14,
                    })}
                  </div>
                  <span className="whitespace-nowrap">{prompt.title}</span>
                </div>
              </Button>
            </motion.div>
          ))}
        </div>

        <Button
          variant="ghost"
          size="sm"
          onClick={handleRefresh}
          className="absolute -top-4 right-1 h-5 w-5 p-0 rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-200 hover:bg-neutral-100 dark:hover:bg-neutral-800"
        >
          <motion.div
            animate={{ rotate: isRefreshing ? 360 : 0 }}
            transition={{ duration: 0.3, ease: 'easeInOut' }}
          >
            <RefreshCw size={10} className="text-muted-foreground" />
          </motion.div>
        </Button>
      </div>
    </div>
  );
};
