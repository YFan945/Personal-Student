# Example: AI Learning Report

## Topic

How university students use AI tools in coursework.

## Confirmed Constraints

- Type: coursework report
- Language: Chinese
- Duration: 8 minutes
- Slides: 10
- Format: group, 4 members
- Image source: ask before web search; generated diagrams allowed

## Outline

### Slide 1: 我们关注的是 AI 如何参与作业过程

- Main content: topic, course, team members
- Visual suggestion: title page with translucent panel and simple workflow shapes
- Speaker note: introduce the topic and why it relates to daily coursework
- Transition: 先从我们观察到的一个具体现象说起。

### Slide 2: 大多数使用发生在“开始写之前”

- Main content: idea generation, outline support, wording polishing
- Visual suggestion: three-step process diagram
- Speaker note: explain that AI is often used as support, not direct replacement
- Transition: 这个现象背后有三个主要原因。

### Slide 3: 便利性是最直接的原因

- Main content: fast response, low starting pressure, easy revision
- Visual suggestion: comparison cards
- Speaker note: connect the reasons with student workload
- Transition: 但便利性也带来了可靠性问题。

### Slide 4: 可靠性问题主要出现在事实和引用上

- Main content: invented facts, unclear sources, outdated examples
- Visual suggestion: warning callout plus source-check checklist
- Speaker note: explain why students still need verification
- Transition: 所以我们不能只看“能不能生成”，还要看“怎么使用”。

### Slide 5: 我们把使用过程分成三个阶段

- Main content: before writing, during writing, after writing
- Visual suggestion: horizontal timeline with three nodes
- Speaker note: show where AI helps and where human judgment remains necessary
- Transition: 接下来用一个小组作业场景说明。

### Slide 6: 小组作业中，AI 更适合做辅助分工

- Main content: collect ideas, compare outlines, polish wording
- Visual suggestion: four-member collaboration diagram
- Speaker note: connect the topic with real group work
- Transition: 但如果直接交给 AI 完成，就会出现新的风险。

### Slide 7: 直接套用 AI 内容会削弱学生自己的判断

- Main content: same wording, weak evidence, hard to answer questions
- Visual suggestion: before/after text comparison cards
- Speaker note: explain AI-like wording and defense risk
- Transition: 因此我们更推荐一种有限使用方式。

### Slide 8: 更合理的做法是“先用 AI，再人工筛选”

- Main content: generate options, verify sources, rewrite in own words
- Visual suggestion: loop diagram with three steps
- Speaker note: provide practical advice for classmates
- Transition: 这个建议也有边界。

### Slide 9: 我们的结论只适用于一般课程作业场景

- Main content: limited sample, course differences, tool differences
- Visual suggestion: limitation panel with three concise points
- Speaker note: show modest conclusion and avoid overclaiming
- Transition: 最后回到最初的问题。

### Slide 10: AI 可以帮我们开始，但不能替我们完成判断

- Main content: final takeaway, thank you, Q&A
- Visual suggestion: summary card plus Q&A shape marker
- Speaker note: close with a clear student-like conclusion
- Transition: 以上是我们的汇报，请老师和同学批评指正。

## Slide Spec YAML

```yaml
meta:
  topic: "AI 如何参与作业过程"
  presentation_type: "coursework report"
  language: "Chinese"
  duration_min: 8
  slide_count: 10
  format: "group"
  members: ["A", "B", "C", "D"]
  course: "Introduction to AI"
  image_source: "ask-before-web-search"
  output_prefix: "ai-learning-report"
slides:
  - id: 1
    title: "我们关注的是 AI 如何参与作业过程"
    layout: "title"
    content:
      bullets:
        - "课程汇报"
        - "小组成员"
    visual:
      type: "workflow-shapes"
      purpose: "Show AI as part of the coursework process"
    note_goal: "Introduce the topic naturally"
    transition: "先从我们观察到的一个具体现象说起。"
    timing_sec: 35
    owner: "A"
  - id: 2
    title: "大多数使用发生在“开始写之前”"
    layout: "process"
    content:
      bullets:
        - "想法生成"
        - "大纲支持"
        - "语言润色"
    visual:
      type: "three-step-process"
      purpose: "Explain the main use stages"
    note_goal: "Explain the process without reading the slide"
    transition: "这个现象背后有三个主要原因。"
    timing_sec: 50
    owner: "A"
  - id: 3
    title: "便利性是最直接的原因"
    layout: "comparison-cards"
    content:
      bullets:
        - "响应快"
        - "降低开头压力"
        - "便于反复修改"
    visual:
      type: "three-card-comparison"
      purpose: "Show why students start with AI"
    note_goal: "Connect convenience with coursework pressure"
    transition: "但便利性也带来了可靠性问题。"
    timing_sec: 50
    owner: "B"
  - id: 4
    title: "可靠性问题主要出现在事实和引用上"
    layout: "risk-callout"
    content:
      bullets:
        - "事实可能不准确"
        - "来源不够清楚"
        - "案例可能过时"
    visual:
      type: "warning-callout"
      purpose: "Highlight verification risks"
    note_goal: "Explain why generated content still needs checking"
    transition: "所以我们不能只看“能不能生成”，还要看“怎么使用”。"
    timing_sec: 50
    owner: "B"
  - id: 5
    title: "我们把使用过程分成三个阶段"
    layout: "timeline"
    content:
      bullets:
        - "写作前：找方向"
        - "写作中：理结构"
        - "写作后：改表达"
    visual:
      type: "horizontal-timeline"
      purpose: "Map AI use to coursework stages"
    note_goal: "Clarify where AI helps and where judgment is needed"
    transition: "接下来用一个小组作业场景说明。"
    timing_sec: 45
    owner: "B"
  - id: 6
    title: "小组作业中，AI 更适合做辅助分工"
    layout: "team-workflow"
    content:
      bullets:
        - "收集想法"
        - "比较大纲"
        - "统一表达"
    visual:
      type: "member-workflow"
      purpose: "Show AI as a group coordination aid"
    note_goal: "Use a concrete group-work example"
    transition: "但如果直接交给 AI 完成，就会出现新的风险。"
    timing_sec: 50
    owner: "C"
  - id: 7
    title: "直接套用 AI 内容会削弱学生自己的判断"
    layout: "before-after"
    content:
      bullets:
        - "表达相似"
        - "证据薄弱"
        - "答辩困难"
    visual:
      type: "before-after-text-cards"
      purpose: "Compare AI-like text with student rewriting"
    note_goal: "Explain AI wording risk and defense risk"
    transition: "因此我们更推荐一种有限使用方式。"
    timing_sec: 50
    owner: "C"
  - id: 8
    title: "更合理的做法是“先用 AI，再人工筛选”"
    layout: "loop-diagram"
    content:
      bullets:
        - "生成多个选项"
        - "核查来源"
        - "用自己的话重写"
    visual:
      type: "three-step-loop"
      purpose: "Turn the finding into practical advice"
    note_goal: "Give classmates a usable method"
    transition: "这个建议也有边界。"
    timing_sec: 50
    owner: "D"
  - id: 9
    title: "我们的结论只适用于一般课程作业场景"
    layout: "limitations"
    content:
      bullets:
        - "样本有限"
        - "课程要求不同"
        - "工具能力不同"
    visual:
      type: "three-limit-panels"
      purpose: "Show honest scope and avoid overclaiming"
    note_goal: "State limitations clearly"
    transition: "最后回到最初的问题。"
    timing_sec: 45
    owner: "D"
  - id: 10
    title: "AI 可以帮我们开始，但不能替我们完成判断"
    layout: "summary-qa"
    content:
      bullets:
        - "辅助开始"
        - "人工判断"
        - "谢谢观看 / Q&A"
    visual:
      type: "summary-card"
      purpose: "Close with one memorable takeaway"
    note_goal: "End naturally and invite questions"
    transition: "以上是我们的汇报，请老师和同学批评指正。"
    timing_sec: 45
    owner: "D"
```

## Speaker Notes Sample

Slide 4:
可靠性问题主要集中在事实和引用上。比如 AI 有时会把不存在的来源说得很像真的，或者使用已经过时的案例。所以我们小组认为，AI 可以帮助整理信息，但不能替代查证过程。

Slide 10:
最后回到我们的核心观点：AI 可以帮我们开始，但不能替我们完成判断。对课程作业来说，更重要的不是完全不用 AI，而是知道哪些部分可以借助它，哪些部分必须由我们自己负责。以上是我们的汇报，请老师和同学批评指正。

## Expected PPTX Outputs

- `outputs/ai-learning-report-presentation.pptx`
- `outputs/ai-learning-report-speaker-notes.md`
- `outputs/ai-learning-report-preview.png`
