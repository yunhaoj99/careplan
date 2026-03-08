# Care Plan Generator — Design Document

> **Version:** v0.1 (Draft)
> **Date:** 2026-03-08
> **Author:** [Your Name]
> **Status:** Awaiting Review

---

## 1. Background & Motivation

### 1.1 客户是谁

A specialty pharmacy（类似 CVS 的专业药房）。

### 1.2 痛点

- 药剂师目前**手动编写** care plan，每个患者耗时 **20–40 分钟**
- Care plan 是 compliance 必需品，也是向 Medicare 和药企报销的依据
- 人手严重不足，任务大量积压

### 1.3 目标

构建一个 web 工具，让医疗工作者（medical assistant）输入患者信息后，**自动调用 LLM 生成 care plan**，从 20–40 分钟缩短到几分钟。

---

## 2. Users & Workflow

### 2.1 用户

| 角色 | 说明 |
|---|---|
| Medical Assistant | 主要用户，负责在 web 表单中录入患者和订单信息 |
| Pharmacist | 审核生成的 care plan，打印后交给患者 |

> **患者不接触本系统。**

### 2.2 核心工作流

```
Medical Assistant 录入患者信息 + 药物信息
        ↓
   系统验证输入 + 重复检测
        ↓
  （通过）调用 LLM 生成 Care Plan
        ↓
  用户下载 Care Plan 文件
        ↓
  （可选）导出报告给药企
```

---

## 3. Data Model（初步）

### 3.1 输入字段

| 字段 | 类型 | 验证规则 |
|---|---|---|
| Patient First Name | string | 必填 |
| Patient Last Name | string | 必填 |
| Patient MRN | string | 必填，唯一，6 位数字 |
| Patient DOB | date | 必填 |
| Referring Provider Name | string | 必填 |
| Referring Provider NPI | string | 必填，10 位数字 |
| Primary Diagnosis | string | 必填，ICD-10 格式（如 `G70.0`） |
| Additional Diagnoses | list of string | 可选，每项须为 ICD-10 格式 |
| Medication Name | string | 必填 |
| Medication History | list of string | 可选 |
| Patient Records | string 或 PDF | 可选 |

### 3.2 核心实体（初步）

```
Patient       — 患者信息（MRN 为唯一标识）
Provider      — 医生信息（NPI 为唯一标识）
Order         — 一次用药订单（关联 Patient + Provider + Medication）
CarePlan      — LLM 生成的结果（关联 Order，一个订单对应一个 care plan）
```

> 具体的数据库表设计在后续迭代中完善。

---

## 4. Care Plan 规范

### 4.1 生成单位

**一个 care plan 对应一个 order（一种药物）。**

如果同一患者有多种药物，每种药物分别生成独立的 care plan。

### 4.2 输出必须包含

| 章节 | 说明 |
|---|---|
| **Problem List / Drug Therapy Problems** | 当前药物治疗中存在的问题 |
| **Goals (SMART)** | 具体、可衡量、有时限的治疗目标 |
| **Pharmacist Interventions / Plan** | 药剂师的干预措施（剂量、给药方式、监测等） |
| **Monitoring Plan** | 需要监测的指标和时间表 |

### 4.3 输出格式

- 文本文件，用户可下载

---

## 5. Validation & Duplicate Detection Rules

### 5.1 输入验证

| 规则 | 说明 |
|---|---|
| NPI | 必须是 10 位纯数字 |
| MRN | 必须是 6 位纯数字 |
| ICD-10 | 须符合 ICD-10 格式（字母开头 + 数字，如 `G70.0`, `I10`） |
| 必填字段 | 所有标记为"必填"的字段不能为空 |

### 5.2 重复检测规则

| 场景 | 处理方式 | 原因 |
|---|---|---|
| 同一患者 + 同一药物 + **同一天** | ❌ **ERROR** — 阻止提交 | 肯定是重复提交 |
| 同一患者 + 同一药物 + **不同天** | ⚠️ **WARNING** — 用户确认后可继续 | 可能是续方（refill） |
| MRN 相同 + 名字或 DOB 不同 | ⚠️ **WARNING** — 用户确认后可继续 | 可能是录入错误 |
| 名字 + DOB 相同 + MRN 不同 | ⚠️ **WARNING** — 用户确认后可继续 | 可能是同一人不同 MRN |
| NPI 相同 + Provider 名字不同 | ❌ **ERROR** — 必须修正 | NPI 是唯一标识，不能有冲突 |

### 5.3 ERROR vs WARNING 的区别

- **ERROR**：阻止提交，用户必须修正后才能继续
- **WARNING**：弹出提示，用户可以选择"确认继续"或"返回修改"

---

## 6. Functional Requirements

| # | 功能 | 优先级 | 说明 |
|---|---|---|---|
| F1 | Web 表单录入患者 + 订单信息 | ✅ P0 | 核心入口 |
| F2 | 输入验证（格式、必填） | ✅ P0 | 数据质量保证 |
| F3 | 患者 / 订单重复检测 | ✅ P0 | 不能打乱现有工作流 |
| F4 | Provider 重复检测 | ✅ P0 | 影响 pharma 报告准确性 |
| F5 | 调用 LLM 生成 Care Plan | ✅ P0 | 核心价值 |
| F6 | Care Plan 下载 | ✅ P0 | 用户需要上传到他们自己的系统 |
| F7 | 导出报告（pharma reporting） | ✅ P0 | 向药企报告所需 |

---

## 7. Non-Functional / Production-Ready Requirements

| 要求 | 说明 |
|---|---|
| 输入验证 | 所有用户输入必须经过验证 |
| 数据完整性 | 外键关系、唯一约束等必须在数据库层面保证 |
| 错误处理 | 错误信息必须安全、清晰、不暴露 stack trace 或 PHI（患者隐私信息） |
| 代码结构 | 模块化，易于导航和维护 |
| 自动化测试 | 关键业务逻辑必须有 unit test 和 integration test |
| 开箱即用 | 项目 clone 下来后可以直接运行（Docker） |

---

## 8. Tech Stack（初步）

| 类别 | 技术 | 选择原因 |
|---|---|---|
| Backend | Python + Django + DRF | 适合快速开发 REST API，生态成熟 |
| Frontend | React | 组件化开发，适合表单类应用 |
| Database | PostgreSQL | 关系型数据库，适合有复杂关系的业务数据 |
| LLM | Claude API 或 OpenAI API | 生成 care plan 的核心能力 |
| Containerization | Docker + Docker Compose | 保证开发环境一致，满足"开箱即用"要求 |

> 后续可能引入：Redis（消息队列）、Celery（异步任务）、AWS 部署等。

---

## 9. Open Questions

| # | 问题 | 状态 |
|---|---|---|
| Q1 | Patient Records 为 PDF 时，是否需要解析内容（OCR）？还是直接传给 LLM？ | 待确认 |
| Q2 | 导出报告的具体字段和格式（CSV? Excel?）？ | 待确认 |
| Q3 | 是否需要用户登录和权限管理（Phase 1）？ | 待确认 |
| Q4 | Care plan 生成后是否允许重新生成或编辑？ | 待确认 |
| Q5 | MRN 在示例中为 8 位（00012345），但需求写 6 位，以哪个为准？ | 待确认 |

---

## Appendix: Sample Input & Output

### Sample Input

```
Name: A.B.
MRN: 00012345
DOB: 1979-06-08
Sex: Female
Weight: 72 kg
Allergies: None known
Medication: IVIG
Primary Diagnosis: Generalized myasthenia gravis (G70.0)
Secondary Diagnoses: Hypertension (I10), GERD (K21.0)
Home Meds: Pyridostigmine 60mg, Prednisone 10mg, Lisinopril 10mg, Omeprazole 20mg
```

### Sample Output (Care Plan)

```
Problem List / Drug Therapy Problems (DTPs)
- Need for rapid immunomodulation to reduce myasthenic symptoms
- Risk of infusion-related reactions
- Risk of renal dysfunction or volume overload
- Risk of thromboembolic events
- Potential drug–drug interactions
- Patient education / adherence gap

Goals (SMART)
- Primary: Achieve clinically meaningful improvement in muscle strength within 2 weeks
- Safety: No severe infusion reaction, no acute kidney injury
- Process: Complete full 2 g/kg course with documented monitoring

Pharmacist Interventions / Plan
- Dosing & Administration
- Premedication
- Infusion rates & titration
- Hydration & renal protection
- Monitoring during infusion
- Adverse event management

Monitoring Plan & Lab Schedule
- Before first infusion: CBC, BMP, baseline vitals
- During each infusion: Vitals q15–30 min
- Post-course (3–7 days): BMP to check renal function
```
