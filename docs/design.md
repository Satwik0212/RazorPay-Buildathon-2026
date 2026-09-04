# Design Guide — Razorpay AI Commerce Intelligence

**Project:** Razorpay AI Buildathon 2026 — Track 01: AI Growth & Agentic Commerce  
**Frontend:** React / JavaScript  
**Design target:** Razorpay-native, fintech-grade, AI-native, trustworthy, modern  
**Primary theme:** Light  
**Secondary theme:** Dark where useful for AI/system states  
**Design language reference:** RazorSense

---

# 1. Design Goal

The frontend should immediately feel like:

> **"This could be a real Razorpay product."**

Not:

- a generic hackathon dashboard
- a purple AI SaaS template
- a flashy chatbot
- a Tailwind component collection
- an over-animated AI demo

The visual identity should combine:

```text
Razorpay
+
Fintech trust
+
AI intelligence
+
Merchant analytics
+
Agentic commerce
```

The interface should feel:

```text
clean
sharp
confident
technical
alive
trustworthy
fast
```

---

# 2. Official Razorpay Design Direction

Razorpay has introduced **RazorSense**, its newer design language.

Razorpay describes RazorSense as:

> "built for the humans in the AI era"

Its design philosophy emphasizes:

```text
every state has a feeling
every interaction has a pulse
interfaces feel alive
```

RazorSense also says its shapes and angles are derived from the Razorpay glyph, while its "Flutes" provide dynamic motion and contextual response.

The official RazorSense page explicitly showcases components/states such as:

```text
Card
Button
Insights
Skeleton Loader
Thinking State
Ray Loading
Progress Bar
Success State
```

Therefore, our design should not simply copy an old Razorpay dashboard aesthetic.

We should take inspiration from the **current RazorSense direction** while keeping our own product implementation original.

Source:

https://razorpay.com/razorsense/

---

# 3. Brand Foundation

Razorpay's current public interfaces consistently use a strong purple identity.

Razorpay documentation currently gives:

```text
#6822CC
```

as an example Razorpay brand/theme color for checkout, Webstore and Payment Button customization.

Therefore:

## Primary brand

```text
Razorpay Purple
#6822CC
```

Use it for:

```text
primary actions
active navigation
important highlights
AI accents
links
focus states
selected states
```

Do NOT use purple everywhere.

Purple should communicate:

> "This is the important/actionable layer."

---

# 4. Recommended Colour System

Use CSS variables/tokens.

```css
:root {
  --rzp-primary: #6822CC;
  --rzp-primary-hover: #5B1DB3;
  --rzp-primary-soft: #F1EAFE;

  --rzp-bg: #F7F7F9;
  --rzp-surface: #FFFFFF;
  --rzp-surface-subtle: #FAFAFC;

  --rzp-text: #171717;
  --rzp-text-secondary: #5F6368;
  --rzp-text-muted: #8A8F98;

  --rzp-border: #E7E7EC;
  --rzp-border-strong: #D8D8E0;

  --rzp-success: #159447;
  --rzp-success-soft: #EAF8F0;

  --rzp-warning: #B76E00;
  --rzp-warning-soft: #FFF5DF;

  --rzp-danger: #D92D20;
  --rzp-danger-soft: #FEECEB;

  --rzp-info: #2563EB;
  --rzp-info-soft: #EEF4FF;

  --rzp-ai: #7C3AED;
  --rzp-ai-soft: #F3E8FF;
}
```

These are project design tokens.

They are not presented as an official complete Razorpay brand palette.

The official Razorpay documentation confirms `#6822CC` as a currently used example theme colour. citeturn0search1turn0search2

---

# 5. Colour Hierarchy

Use roughly:

```text
70% neutral surfaces
20% text/borders
8% purple/brand
2% semantic colours
```

The UI should NOT look like:

```text
████ purple everywhere
```

Instead:

```text
white / near-white
        +
black text
        +
subtle borders
        +
purple moments
```

This keeps the interface fintech-like.

---

# 6. AI Colour

AI should have its own visual identity, but it must still belong to Razorpay.

Use:

```text
AI Purple
#7C3AED
```

with soft backgrounds:

```text
#F3E8FF
```

AI components can use:

```text
purple glow
purple border
purple icon
purple gradient
```

but avoid neon cyberpunk styling.

The AI should feel:

```text
intelligent
calm
precise
```

not:

```text
experimental
chaotic
sci-fi
```

---

# 7. Semantic Colours

## Success

```text
#159447
```

Use for:

```text
payment success
simulation improvement
approved optimization
completed job
verified webhook
```

## Warning

```text
#B76E00
```

Use for:

```text
review required
simulation uncertainty
low confidence
inventory warning
```

## Error

```text
#D92D20
```

Use for:

```text
payment failed
invalid AI action
blocked authorization
webhook verification failure
```

## Information

```text
#2563EB
```

Use sparingly for:

```text
neutral information
system state
help
```

---

# 8. Background

Primary application background:

```text
#F7F7F9
```

Cards:

```text
#FFFFFF
```

Avoid a pure white application background across the entire screen.

Use:

```text
soft grey canvas
+
white surfaces
```

This gives dashboards depth without requiring shadows everywhere.

---

# 9. Dark Mode

Dark mode is optional.

Do NOT spend major development time creating two complete themes before the core product works.

If implemented:

```text
background:
#0F0F12

surface:
#17171C

surface elevated:
#1E1E25

text:
#F7F7F8

secondary:
#A5A5B0

border:
#2A2A33

primary:
#8B5CF6
```

The AI simulation view could use a dark presentation mode if it makes the visualization more compelling.

Razorpay documentation itself supports dark-mode customization for some widgets, so dark UI is compatible with parts of the broader product ecosystem. citeturn0search7

---

# 10. Typography

Primary recommendation:

```text
Inter
```

Fallback:

```text
system-ui
-apple-system
BlinkMacSystemFont
"Segoe UI"
sans-serif
```

Typography should be:

```text
clean
compact
highly readable
```

Avoid:

```text
Poppins everywhere
Montserrat
futuristic display fonts
```

This is a fintech product, not a gaming landing page.

---

# 11. Type Scale

Recommended:

```text
Display:       40–48px
Page heading:   28–32px
Section title:  20–24px
Card title:     16–18px
Body:           14–16px
Secondary:      13–14px
Caption:        12px
```

Use weight:

```text
Display: 700
Heading: 650–700
Body: 400–500
Labels: 500–600
```

Do not make every heading bold.

---

# 12. Logo

Use the official Razorpay logo/assets where permitted.

Do not redraw the logo.

Do not:

```text
change proportions
rotate
stretch
add gradients
put random glow around it
```

Razorpay provides official brand assets through its Newsroom.

Source:

https://razorpay.com/newsroom/brand-assets/

Razorpay states that its trademarks and brand elements are subject to its Usage Agreement. citeturn0search4

---

# 13. Application Shell

Desktop layout:

```text
┌─────────────────────────────────────────────────────────────┐
│ Razorpay logo     AI Commerce Intelligence       Profile    │
├──────────────┬──────────────────────────────────────────────┤
│              │                                              │
│ Overview     │                                              │
│ Catalogue    │                MAIN CONTENT                   │
│ AI Buyers    │                                              │
│ Simulations  │                                              │
│ Optimizations│                                              │
│ Experiments  │                                              │
│ Transactions │                                              │
│ Analytics    │                                              │
│              │                                              │
│ Settings     │                                              │
└──────────────┴──────────────────────────────────────────────┘
```

Sidebar:

```text
240–260px
```

Main content:

```text
max-width: 1440px
```

Content padding:

```text
24–40px
```

---

# 14. Sidebar

The sidebar should be quiet.

Not:

```text
huge icons
rainbow gradients
```

Use:

```text
small icon
label
active state
```

Active item:

```text
soft purple background
purple text
small left indicator or subtle pill
```

Example:

```text
◉ Overview

▣ Catalogue

✦ AI Buyers
  ├ Simulation
  ├ Scenarios

✧ Optimizations

⌁ Experiments

₹ Transactions

▤ Analytics
```

---

# 15. Navigation Structure

Recommended:

```text
Overview

Commerce
  Catalogue
  Orders
  Transactions

AI Intelligence
  AI Buyers
  Simulations
  Insights
  Optimizations

Growth
  Experiments
  Offers
  Campaigns

System
  Audit
  Settings
```

P2 items should remain hidden until implemented.

Do not show dead navigation.

---

# 16. Dashboard Design

The dashboard should answer three questions immediately:

```text
How is my commerce performing?

What is AI seeing?

What should I do next?
```

Top row:

```text
GMV
Orders
Conversion
AI Buyer Match Rate
```

Second row:

```text
AI Buyer Simulation
Optimization Opportunities
Recent Transactions
```

Third row:

```text
Top Frictions
Recent Improvements
```

---

# 16.1 Simulation vs Real Transactions Visual

The dashboard must explicitly visually separate real financial truth from simulated AI experiments:

```text
Merchant Dashboard
├── Real Transactions
│   └── 100% deterministic (cart -> quote -> policy -> payment)
└── Simulated Transactions
    └── AI buyer (persona -> search -> score -> select)
```

---

# 17. Metric Cards

Example:

```text
AI Buyer Match Rate

78.4%

↑ 16.2% vs baseline

1,000 buyers simulated
```

Card design:

```text
white
1px border
12–16px radius
subtle shadow only when needed
```

Do not overuse gradients.

---

# 18. The Hero Metric

The most important dashboard metric should be:

```text
AI Buyer Match Rate
```

because it connects directly to our product thesis.

Secondary:

```text
Constraint Satisfaction
Simulated Conversion
Optimization Impact
```

---

# 19. AI Buyer Simulation Screen

This should be the visually strongest screen.

Possible layout:

```text
┌─────────────────────────────────────────────────────────────┐
│ AI Buyer Simulation                           Run Simulation │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  BUYERS                         RESULTS                      │
│                                                             │
│  Budget Buyer      250         Match Rate     78%           │
│  Quality Buyer     250         ↑ 16%                        │
│  Speed Buyer       250         Friction       18%           │
│  Deal Seeker       250         Avg Decision   1.2s          │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Simulation Activity                                        │
│                                                             │
│  ◉ Buyer evaluating product...                              │
│  ◉ Checking budget...                                       │
│  ◉ Checking delivery...                                     │
│  ✓ Decision made                                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

# 20. AI "Thinking" State

Use a subtle animated state.

Example:

```text
✦ Analysing buyer constraints
```

with a small moving pulse.

Do NOT show:

```text
AI IS THINKING...
████████████
```

as a fake loading bar.

Instead show actual stages:

```text
Understanding intent
      ↓
Searching catalogue
      ↓
Evaluating constraints
      ↓
Selecting product
      ↓
Recording outcome
```

---

# 21. Simulation Animation

When a simulation runs:

```text
Idle
 ↓
Preparing scenarios
 ↓
Buyer agents appear
 ↓
Evaluation progresses
 ↓
Results aggregate
 ↓
Insights emerge
```

Animation should feel like:

```text
data moving
```

not:

```text
cartoon characters flying around
```

---

# 22. "Ray" / Pulse Motif

RazorSense explicitly references "Flutes" as its dynamic interaction engine and describes the interface as having a living pulse.

We can interpret that visually through:

```text
thin animated lines
soft pulses
small rays
```

Example:

```text
      ────────╲
               ╲
      ●─────────●
               ╱
      ────────╱
```

Use this around:

```text
AI activity
simulation progress
data flow
success states
```

Keep it subtle.

---

# 23. Do NOT Overuse Animation

Animation rules:

```text
Fast interaction:
120–180ms

Standard:
200–250ms

Complex transition:
300–450ms

Never:
> 600ms for ordinary UI
```

The user should feel:

```text
responsive
```

not:

```text
waiting for the animation
```

---

# 24. Recommended Animations

## Button hover

```text
scale: 1 → 1.01
background transition
```

Very subtle.

---

## Card hover

```text
translateY(-1px)
border slightly stronger
```

No giant biginting cards.

---

## Page transition

```text
opacity
+
translateY(4px)
```

150–200ms.

---

## Modal

```text
opacity 0 → 1
scale .98 → 1
```

200ms.

---

# 25. Loading States

Use skeletons for:

```text
dashboard cards
tables
catalogue
simulation results
analytics
```

Use an AI thinking state for:

```text
LLM reasoning
simulation
optimization generation
```

RazorSense explicitly includes skeleton loaders and thinking states as design components. citeturn0search14

---

# 26. Simulation Progress

Instead of:

```text
Loading...
```

show:

```text
Running AI buyer simulation

██████████████░░░░░░  72%

724 / 1000 buyers evaluated
```

Below:

```text
Current phase
Evaluating product compatibility
```

---

# 27. Optimization Card

Example:

```text
┌───────────────────────────────────────────────┐
│ ✦ High-impact opportunity                     │
│                                               │
│ Add delivery-time information                 │
│                                               │
│ 183 simulated buyers could not determine      │
│ delivery eligibility.                         │
│                                               │
│ Expected simulation impact                    │
│ +12.4 percentage points                       │
│                                               │
│ Confidence 86%                                │
│                                               │
│ [Review]                 [Run What-if]         │
└───────────────────────────────────────────────┘
```

This should be one of the most polished components.

---

# 28. AI Recommendations Must Feel Explainable

Never show:

```text
AI recommends this.
```

Show:

```text
Why?

18.3% of simulated buyers rejected products
because delivery information was unavailable.

Evidence:
183 / 1000 scenarios

Confidence:
86%
```

This directly supports our product thesis.

---

# 29. What-If Visualization

This is a major demo moment.

Show:

```text
BEFORE                         AFTER

Match Rate                     Match Rate

62%                            78%

██████████░░░░                 █████████████░

                            +16 pp
```

Then:

```text
Changed:
Delivery information

Simulated buyers:
1,000

Improvement:
+16 percentage points
```

---

# 30. Product Catalogue

Use a dense but clean table.

Columns:

```text
Product
Category
Price
Inventory
AI Readiness
Issues
Actions
```

Example:

```text
Wireless ANC Headphones
Headphones
₹4,999
42
● 82%
2 issues
...
```

AI Readiness should be a project-specific metric, not represented as an official Razorpay metric.

---

# 31. AI Readiness Badge

Use:

```text
High
Medium
Needs improvement
```

Not:

```text
100% AI Ready
```

because that implies false certainty.

---

# 32. Transaction Screen

This must feel extremely trustworthy.

Show:

```text
Order ID
Razorpay Order ID
Amount
Currency
Payment Status
Payment ID
Webhook Status
Created At
```

Use clear status badges:

```text
● PAID
● FAILED
● PENDING
● VERIFYING
```

---

# 33. Payment Success

Do not make success look like a confetti party.

Use:

```text
✓ Payment verified

₹4,999

Payment ID
pay_xxxxx

Razorpay Order
order_xxxxx
```

Then:

```text
Verified by server
```

This reinforces trust.

---

# 34. Payment Failure

Example:

```text
Payment could not be completed

Reason:
Payment failed

No duplicate charge was created.

[Try again]
```

Avoid blaming:

```text
"AI couldn't process your payment."
```

---

# 35. Security / Audit Screen

This can be a powerful hackathon differentiator.

Example:

```text
Transaction Audit

10:31:02
Quote created

10:31:04
Authorization approved

10:31:05
Razorpay order created

10:31:28
Payment initiated

10:31:30
Webhook received

10:31:30
Signature verified

10:31:31
Payment marked PAID
```

Use a vertical timeline. Make it explicit that audit events happen AFTER deterministic decisions, not before.

**Correct:** AI → Quote → Decision (Allow/Block) → Audit Event
**Incorrect:** AI → Audit → Quote

---

# 36. Failure Demo UI & Webhook State Machine

When demonstrating a failure or duplicate event:

```text
Webhook received
      ↓
Duplicate event detected
      ↓
No state mutation
      ↓
Audit recorded
```

**Safe Webhook Processing State Machine Flow:**
`Receive webhook -> verify signature -> check idempotency -> evaluate current state -> transition state`

Use:

```text
warning
+
clear explanation
```

not a scary red screen.

---

# 37. AI Agent Interface

If we include conversational UI:

Keep it compact.

```text
┌──────────────────────────────────────┐
│ ✦ Commerce Assistant                 │
│                                      │
│ "Why are AI buyers dropping off?"    │
│                                      │
│ 18.3% are failing delivery checks.   │
│                                      │
│ [View evidence] [Run simulation]     │
└──────────────────────────────────────┘
```

The chat should not become the entire product.

The dashboard remains primary.

---

# 38. AI Chat Rules

AI messages should contain:

```text
answer
+
evidence
+
action
```

Example:

```text
I found a recurring issue.

18.3% of simulated buyers could not determine
delivery eligibility.

Would you like me to run a what-if simulation
with delivery information added?

[Run simulation]
```

This is much better than:

```text
"Sure! I can help optimize your store."
```

---

# 39. Buttons

Primary:

```text
background: #6822CC
text: white
```

Secondary:

```text
white
border: #D8D8E0
text: #171717
```

Tertiary:

```text
transparent
purple text
```

Danger:

```text
white / soft red
red text
```

---

# 40. Button Shapes

Razorpay documentation currently exposes rounded and sharp border options in checkout styling, so both forms exist in the ecosystem. citeturn0search0

For our application:

```text
8px radius
```

for most buttons.

Use:

```text
10–12px
```

for larger cards/containers.

Avoid:

```text
9999px pill buttons everywhere.
```

Pills should be reserved for:

```text
status
tags
filters
```

---

# 41. Cards

Default:

```text
background: #FFFFFF
border: 1px solid #E7E7EC
border-radius: 12px
```

Shadow:

```text
0 1px 2px rgba(...)
```

only when needed.

Prefer borders over heavy shadows.

---

# 42. Border Philosophy

Use borders to create structure.

```text
#E7E7EC
```

Sections should feel:

```text
separated
```

not:

```text
biginting
```

---

# 43. Tables

Table style:

```text
compact
high information density
clear row hover
sticky header where useful
```

Header:

```text
12px
uppercase or sentence case
medium weight
muted colour
```

Rows:

```text
52–60px
```

Avoid giant rows.

---

# 44. Charts

Use restrained charts.

Recommended:

```text
line chart
bar chart
stacked bar
funnel
heatmap
```

Avoid:

```text
3D pie charts
radial explosions
unnecessary gradients
```

---

# 45. AI Buyer Distribution Chart

Example:

```text
Buyer types

Budget         ███████████████ 31%
Quality        ███████████      24%
Speed          █████████         18%
Deal seeker    ███████           15%
Other          █████             12%
```

Use the primary purple as the dominant chart colour and semantic colours only when meaning requires them.

---

# 46. Simulation Funnel

Excellent visualization:

```text
1,000 AI Buyers
      ↓
920 found category
      ↓
842 found matching products
      ↓
781 satisfied constraints
      ↓
742 selected product
      ↓
701 reached checkout
```

This immediately communicates:

```text
where merchants lose buyers
```

---

# 47. Friction Heatmap

Example:

```text
                    Frequency     Severity

Missing delivery      ██████████    High
Compatibility         ███████       High
Price ambiguity       █████         Medium
Description           ███           Low
```

This should be visually simple.

---

# 48. Empty States

Never show:

```text
No data.
```

Instead:

```text
No simulations yet

Run your first AI buyer simulation to discover
where customers may be getting stuck.

[Run simulation]
```

Every empty state should tell the user:

```text
what this screen is
+
why it's empty
+
what to do next
```

---

# 49. Error States

Good:

```text
We couldn't complete the simulation.

Your catalogue was not changed.

Error ID:
sim_123

[Retry]
```

Bad:

```text
500 Internal Server Error
```

The technical error can exist behind an expandable detail.

---

# 50. Toasts

Use toasts for:

```text
saved
approved
rejected
copied
started
completed
```

Do not use toasts for:

```text
critical payment failures
security events
long explanations
```

Those belong in the page.

---

# 51. Modals

Use modals for:

```text
confirmation
approval
dangerous action
small forms
```

Do not put:

```text
entire dashboards
long AI workflows
```

inside modals.

---

# 52. Merchant Approval Flow

For optimization:

```text
Recommendation
      ↓
Evidence
      ↓
Expected impact
      ↓
What-if
      ↓
Merchant approval
      ↓
Apply
```

The approval modal should clearly say:

```text
You are approving a change to:

Delivery information

This will update:
Product metadata

No payment action will be performed.
```

This reduces ambiguity.

---

# 53. AI Confidence

Use:

```text
High confidence
Medium confidence
Low confidence
```

with explanatory evidence.

Do not create fake precision:

```text
87.392%
```

unless there is a legitimate statistical basis.

---

# 54. "Simulation" Must Always Be Visually Distinct

Use a small label:

```text
SIMULATED
```

Example:

```text
+16.2%
SIMULATED IMPROVEMENT
```

This prevents the reviewer from confusing:

```text
simulation
```

with:

```text
real merchant revenue
```

---

# 55. Real vs Simulated Data

Use badges:

```text
LIVE
SIMULATED
TEST MODE
```

Examples:

```text
● LIVE TRANSACTION
◌ SIMULATED BUYER
◉ TEST MODE
```

This is especially important for the hackathon.

---

# 56. Razorpay Payment Integration Visual

When the user enters payment:

```text
Our commerce UI
       ↓
Razorpay Checkout
       ↓
Payment
```

Do not recreate Razorpay Checkout visually.

Let the official Razorpay Checkout UI represent the payment layer.

Our UI should clearly communicate:

```text
Secure payment powered by Razorpay
```

where appropriate and permitted.

---

# 57. Checkout Philosophy

Razorpay's own checkout customization supports:

```text
brand colour
logo
font
border style
sidebar graphics
trusted badge
```

This demonstrates that branded checkout is already part of Razorpay's ecosystem. citeturn0search0

Our demo should therefore integrate with the actual checkout rather than attempting to imitate it.

---

# 58. Responsive Design

Desktop is primary because the merchant dashboard is the main product.

But:

```text
tablet
mobile
```

must remain usable.

Breakpoints:

```text
< 768px
mobile

768–1024px
tablet

> 1024px
desktop
```

On mobile:

```text
sidebar → bottom/slide-out navigation
tables → cards
multi-column dashboard → stacked
```

---

# 59. Grid

Desktop:

```text
12-column grid
```

Common layout:

```text
8 + 4
6 + 6
4 + 4 + 4
```

Gap:

```text
16–24px
```

---

# 60. Spacing Scale

Use:

```text
4
8
12
16
20
24
32
40
48
64
```

Do not randomly use:

```text
13px
19px
27px
```

unless necessary.

---

# 61. Iconography

Use one consistent icon system.

Recommended:

```text
Lucide
```

or an equivalent clean outline icon library.

Icons should be:

```text
16–20px
```

Avoid mixing:

```text
Lucide
Font Awesome
random SVGs
emoji
```

in the same interface.

---

# 62. Emoji Rule

Do not use emojis as primary UI icons.

This is a professional fintech product.

Use:

```text
SVG icon
```

instead.

Emoji may appear in:

```text
empty-state personality
optional AI conversation
```

but sparingly.

---

# 63. AI Icon

Use a custom simple sparkle/star/glyph treatment.

Example:

```text
✦
```

but preferably as an SVG.

AI should visually be:

```text
Razorpay purple
+
small intelligence glyph
```

---

# 64. Motion Language

The entire application should have one motion language.

```text
soft
fast
responsive
purposeful
```

Motion should communicate:

```text
state change
progress
cause → effect
```

not decoration.

---

# 65. Signature Animation

The project can have one signature animation:

```text
Razorpay-purple ray
```

When AI is processing:

```text
────────╲
         ╲
          ✦
         ╱
────────╱
```

The ray gently moves/pulses.

When complete:

```text
✦ → ✓
```

This creates a recognizable AI interaction without copying RazorSense directly.

---

# 66. Simulation Completion Animation

At completion:

```text
progress reaches 100%
       ↓
ray pulse
       ↓
metrics count up
       ↓
insights appear
```

Example:

```text
62%
 ↓
67%
 ↓
71%
 ↓
78%
```

Use a short 400–600ms number transition.

Do not make it excessively dramatic.

---

# 67. Number Animations

Good for:

```text
match rate
orders
simulation count
improvement
```

Avoid animating every number on every render.

Only animate when:

```text
value changes meaningfully
```

---

# 68. Page Transition

Use:

```text
fade + 4px upward movement
```

Duration:

```text
180ms
```

Respect:

```css
prefers-reduced-motion
```

---

# 69. Accessibility

Must support:

```text
keyboard navigation
focus states
ARIA labels
contrast
reduced motion
screen-reader-friendly tables
```

Do not rely only on:

```text
red = failure
green = success
```

Always include:

```text
icon
+
label
```

---

# 70. Focus State

Focus should be obvious.

Use:

```text
2px purple outline
```

not:

```text
remove browser focus
```

---

# 71. AI Safety Visual Language

The UI should visually distinguish:

```text
AI recommendation
```

from:

```text
merchant-approved action
```

Example:

```text
✦ AI Recommendation

[Proposed]

↓ merchant approval

✓ Approved

↓ deterministic application

✓ Applied
```

This is extremely important for the product story.

---

# 72. Financial Safety Visual Language

Use clear states:

```text
PROPOSED
AUTHORIZED
PROCESSING
VERIFIED
PAID
FAILED
BLOCKED
```

Do not use vague states like:

```text
Done
Success-ish
Processing...
```

---

# 73. State Machine Visualization

For transactions:

```text
Quote
  ↓
Authorized
  ↓
Order Created
  ↓
Payment Initiated
  ↓
Webhook Verified
  ↓
Paid
```

If something fails:

```text
Payment Failed
```

not:

```text
Order = Success
```

---

# 74. Security Indicator

A small trust panel can appear during checkout:

```text
✓ Amount verified
✓ Merchant verified
✓ Payment state server-confirmed
✓ Razorpay webhook verified
```

This is more useful than a generic:

```text
🔒 100% secure
```

---

# 75. Dashboard Top Bar

Recommended:

```text
┌───────────────────────────────────────────────────────────┐
│ Razorpay  /  AI Commerce             Search   Help  Akki │
└───────────────────────────────────────────────────────────┘
```

Do not overpopulate it.

---

# 76. Search

Global search can eventually support:

```text
products
orders
simulations
optimizations
```

Keyboard shortcut:

```text
⌘/Ctrl + K
```

Optional P2.

---

# 77. Breadcrumbs

Use where necessary:

```text
AI Buyers / Simulations / SIM-1024
```

Avoid breadcrumbs on every simple page.

---

# 78. Simulation Detail Layout

Recommended:

```text
Header
  Simulation #1024
  Completed
  1,000 buyers

Metrics
  Match Rate
  Satisfaction
  Friction
  Avg Decision Time

Buyer Distribution

Simulation Funnel

Top Frictions

Scenario Table

AI Recommendations

What-if
```

---

# 79. Optimization Detail Layout

```text
Recommendation
       ↓
Problem
       ↓
Evidence
       ↓
Why AI detected it
       ↓
Expected impact
       ↓
What-if
       ↓
Approve / Reject
```

This is a story-driven UI.

---

# 80. Catalogue Readiness Screen

This can become a strong product screen:

```text
Catalogue AI Readiness

Overall:
78 / 100

Product metadata
██████████████░░ 86%

Delivery information
████████░░░░░░░░ 54%

Compatibility
████████████░░░░ 74%

Pricing clarity
███████████████ 92%
```

Again:

> This score is our product metric, not an official Razorpay metric.

---

# 81. Design for the Demo

The final video should visually tell a story.

Recommended flow:

```text
Dashboard
 ↓
Catalogue
 ↓
Run simulation
 ↓
Live AI activity
 ↓
Results
 ↓
Friction
 ↓
Optimization
 ↓
What-if
 ↓
Approve
 ↓
Buyer checkout
 ↓
Razorpay payment
 ↓
Webhook
 ↓
Audit
```

Every screen should support this story.

---

# 82. Demo Mode

Create a seeded demo environment.

Example:

```text
Demo Merchant:
Nova Electronics
```

Catalogue:

```text
50–100 products
```

Simulation:

```text
1,000 buyers
```

This allows the final demo to be deterministic.

---

# 83. Do Not Depend on Live AI During the Entire Pitch

The system should be able to demonstrate:

```text
real AI
```

but also have:

```text
cached/seeded demo results
```

for reliability.

If an external LLM fails during the pitch:

```text
demo should still work
```

The UI should make clear when data is:

```text
precomputed
```

versus:

```text
live run
```

---

# 84. Demo Seed Data

Prepare:

```text
merchant
products
inventory
buyer personas
simulation
frictions
optimizations
test orders
```

before recording.

---

# 85. Visual Hierarchy

Every screen should have:

```text
1 primary thing
2–3 secondary things
everything else supporting
```

Example simulation screen:

```text
PRIMARY:
Match Rate + Simulation Result

SECONDARY:
Friction
Buyer distribution
Optimization

SUPPORTING:
Scenario table
metadata
timestamps
```

---

# 86. Avoid Dashboard Noise

Do not put:

```text
17 KPI cards
8 charts
12 tables
```

on the home page.

The dashboard should be a decision surface.

---

# 87. Design Personality

The final personality should be:

```text
Razorpay:
confident

Fintech:
precise

AI:
alive

Analytics:
clear

Security:
serious
```

Combined:

> **Calm intelligence.**

That should be the visual identity.

---

# 88. What the Product Should NOT Look Like

Avoid:

```text
❌ neon purple cyberpunk
❌ glassmorphism everywhere
❌ giant gradients
❌ excessive rounded pills
❌ biginting 3D AI robots
❌ cartoon agent avatars
❌ excessive shadows
❌ rainbow charts
❌ giant "AI" text
❌ generic ChatGPT clone
❌ excessive animations
```

---

# 89. What It SHOULD Look Like

```text
✓ Razorpay purple
✓ neutral surfaces
✓ strong typography
✓ sharp information hierarchy
✓ subtle rays/pulses
✓ clear states
✓ structured analytics
✓ serious transaction UI
✓ AI recommendations with evidence
✓ clean tables
✓ fast interactions
```

---

# 90. Component System

Create reusable components:

```text
Button
IconButton
Input
Select
Search
Badge
StatusBadge
Card
MetricCard
DataTable
Modal
Drawer
Toast
Tabs
ProgressBar
Skeleton
Timeline
Chart
AIInsightCard
SimulationProgress
OptimizationCard
AuditTimeline
EmptyState
ErrorState
```

---

# 91. Design Tokens in Code

Recommended structure:

```text
src/
└── design/
    ├── tokens.css
    ├── typography.css
    ├── motion.css
    └── components/
```

Tokens:

```text
colour
spacing
radius
shadow
typography
motion
z-index
```

---

# 92. CSS Token Example

```css
:root {
  --color-primary: #6822CC;
  --color-primary-hover: #5B1DB3;

  --color-bg: #F7F7F9;
  --color-surface: #FFFFFF;

  --color-text: #171717;
  --color-text-secondary: #5F6368;

  --color-border: #E7E7EC;

  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 12px;

  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;
}
```

---

# 93. Z-Index

Keep a controlled system:

```text
base: 0
sticky: 10
dropdown: 20
modal: 40
toast: 50
```

Do not randomly use:

```text
z-index: 999999
```

---

# 94. Frontend Architecture

Recommended:

```text
src/
├── app/
├── components/
├── features/
│   ├── auth/
│   ├── catalogue/
│   ├── buyers/
│   ├── simulations/
│   ├── optimizations/
│   ├── checkout/
│   ├── transactions/
│   └── analytics/
├── design/
├── hooks/
├── lib/
├── services/
└── pages/
```

Feature-level styling should consume shared design tokens.

---

# 95. API State

Use a proper server-state library if needed:

```text
TanStack Query
```

rather than manually duplicating:

```text
loading
error
data
cache
refetch
```

for every endpoint.

---

# 96. Simulation Realtime Updates

If implemented:

```text
WebSocket / Server-Sent Events
```

can stream:

```text
simulation progress
buyer events
optimization generation
```

Example:

```text
SSE:
GET /api/v1/optimization/simulations/{id}/stream
```

This is optional.

Polling is acceptable for the hackathon.

---

# 97. Frontend Security

Never store:

```text
Razorpay secret
database credentials
LLM provider secret
webhook secret
```

in the frontend.

Frontend receives only:

```text
public configuration
temporary IDs
safe response data
```

---

# 98. Payment UI Rule

The frontend may display:

```text
₹4,999
```

but that number is informational.

The authoritative amount comes from:

```text
server quote
```

The checkout request must use the server-generated Razorpay Order.

---

# 99. AI UI Rule

AI responses should preferably be structured:

```json
{
  "title": "...",
  "reason": "...",
  "evidence": [],
  "confidence": 0.86,
  "recommended_action": "..."
}
```

Then render them as UI components.

Do not simply dump raw LLM markdown into the application.

---

# 100. Accessibility for AI

AI content should remain understandable without animation.

If the animation disappears:

```text
the information must still make sense.
```

For example:

```text
✦ Analysing buyer constraints...
```

must become:

```text
Analysing buyer constraints
```

with no dependence on the pulsing effect.

---

# 101. Reduced Motion

Respect:

```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms;
    transition-duration: 0.01ms;
  }
}
```

Do not disable meaningful state information.

---

# 102. Performance

The dashboard should feel fast.

Targets:

```text
First meaningful UI:
fast

Navigation:
instant-feeling

Button response:
< 200ms where possible

Long operation:
show immediate progress state
```

Do not block the interface while simulation runs.

---

# 103. Optimistic UI

Safe optimistic updates:

```text
toggle
local preference
non-critical UI state
```

Avoid optimistic updates for:

```text
payment status
authorization
financial amount
inventory
```

Those require server confirmation.

---

# 104. Toast + Server Truth

After:

```text
Approve optimization
```

do not only show:

```text
"Approved!"
```

Refetch/confirm the actual server state.

For financial state:

```text
server state wins
```

always.

---

# 105. Mobile Buyer Experience

If we build the buyer side:

```text
minimal header
product card
AI recommendation
cart
checkout
```

Mobile-first.

The merchant dashboard can remain desktop-first.

---

# 106. Buyer Product Card

```text
┌──────────────────────────────┐
│ Product image                │
│                              │
│ Wireless ANC Headphones      │
│ ₹4,999                       │
│                              │
│ ✓ ANC                        │
│ ✓ 30h battery                │
│ ✓ Delivery in 2 days         │
│                              │
│ [Add to cart]                │
└──────────────────────────────┘
```

---

# 107. AI Recommendation on Buyer Side

Example:

```text
✦ Best match for your request

Wireless ANC Headphones

Why:
✓ Under your ₹5,000 budget
✓ ANC supported
✓ 2-day delivery
✓ 30-hour battery

[Choose]
```

This demonstrates the AI buyer/commercial loop.

---

# 108. Checkout Visual Hierarchy

```text
Product
 ↓
Price
 ↓
Trust
 ↓
Payment method
 ↓
Pay
```

Do not make:

```text
AI explanation
```

more visually dominant than:

```text
amount
```

during payment.

---

# 109. Trust Is a Design Feature

Because this is a payment product:

```text
clarity > decoration
```

Always make these obvious:

```text
who
what
how much
why
status
```

---

# 110. AI Trust Is Also a Design Feature

For AI recommendations:

```text
What happened?
Why?
Evidence?
Confidence?
What will change?
Who approves it?
```

This should be visible.

---

# 111. Recommended Landing / Login

Login should be minimal:

```text
Razorpay
AI Commerce Intelligence

Build for the AI buyer era.

Email
Password

[Sign in]

Merchant dashboard
```

Do not make the login page an enormous marketing site.

---

# 112. Onboarding

Merchant onboarding:

```text
Create merchant
 ↓
Add catalogue
 ↓
Configure policies
 ↓
Run first simulation
```

Progress:

```text
1 / 4
2 / 4
3 / 4
4 / 4
```

---

# 113. Onboarding Animation

Use subtle progress movement:

```text
●────○────○────○
```

Completed:

```text
✓────●────○────○
```

No confetti.

---

# 114. Product Import

Support:

```text
CSV upload
```

with:

```text
drag & drop
```

Example:

```text
Drop your catalogue here

CSV
100 products

[Import catalogue]
```

Show validation:

```text
92 valid
6 missing price
2 missing category
```

---

# 115. Validation UI

Errors should appear next to the field.

Good:

```text
Price
₹-100

Price must be greater than 0.
```

Not:

```text
Something went wrong.
```

---

# 116. Empty Catalogue

If no products:

```text
Your catalogue is empty.

AI buyer simulation needs products
to evaluate.

[Add product]
[Import CSV]
```

---

# 117. Simulation Setup UI

```text
Create Simulation

Buyer types
☑ Budget
☑ Quality
☑ Speed
☐ Deal Seeker

Scenarios
[1000]

Goal
[Maximize buyer satisfaction]

[Run Simulation]
```

---

# 118. Simulation Results UI

At the top:

```text
Simulation #1024
Completed
1,000 buyers
```

Then:

```text
78.4%
AI Buyer Match Rate
```

Then:

```text
Why buyers failed
```

Then:

```text
What should we change?
```

This is the narrative.

---

# 119. Optimization Approval UI

Approval should be deliberate.

```text
Review optimization

Problem
Delivery information missing

Evidence
183 / 1000 buyers affected

Expected simulated impact
+12.4 pp

Risk
Low

Change
Add delivery_days to product metadata

[Reject]
[Approve]
```

---

# 120. Audit UI

Keep it technical.

Example:

```text
Event
OPTIMIZATION_APPROVED

Actor
Merchant Admin

Resource
Product #123

Timestamp
28 Aug 2026 10:31:20

Source
Dashboard

Result
Approved
```

---

# 121. Design Documentation Rule

Every new UI component should answer:

```text
What job does this component perform?
```

If the answer is:

```text
"Looks cool."
```

do not add it.

---

# 122. Visual QA Checklist

Before final demo:

```text
□ Razorpay purple is consistent
□ No random colours
□ Typography consistent
□ Buttons consistent
□ Cards consistent
□ Spacing consistent
□ Tables readable
□ AI states clear
□ Simulated vs real clearly labelled
□ Payment status clear
□ Error states polished
□ Mobile doesn't break
□ No console errors
□ No layout jumps
□ Animations smooth
□ Reduced motion works
```

---

# 123. Final Design Checklist

## Brand

```text
✓ Razorpay visual identity
✓ Official logo usage
✓ #6822CC primary
✓ neutral fintech surfaces
```

## AI

```text
✓ subtle AI purple
✓ evidence-driven insights
✓ thinking states
✓ simulation progress
✓ ray/pulse motion
```

## Fintech

```text
✓ clear amounts
✓ explicit states
✓ audit trail
✓ secure payment presentation
✓ no fake certainty
```

## UX

```text
✓ clear navigation
✓ strong hierarchy
✓ fast interaction
✓ responsive
✓ accessible
```

---

# 124. The One Design Principle

If there is ever a conflict between:

```text
"looks impressive"
```

and:

```text
"makes the product easier to understand"
```

choose:

> **easier to understand.**

A Razorpay reviewer should understand the product without needing us to explain every screen.

---

# 125. Final Visual Direction

The final product should feel like:

```text
Razorpay Dashboard
        +
RazorSense motion
        +
AI-native intelligence
        +
merchant analytics
        +
fintech trust
```

Not:

```text
ChatGPT clone
        +
purple gradient
        +
random dashboard
```

---

# 126. Final Design North Star

> **Calm intelligence inside a trusted payment system.**

Every visual decision should reinforce that.

---

# 127. Official References

- RazorSense — Razorpay's current design language:
  https://razorpay.com/razorsense/

- Razorpay Brand Assets:
  https://razorpay.com/newsroom/brand-assets/

- Razorpay Checkout Styling:
  https://razorpay.com/docs/payments/dashboard/account-settings/checkout-styling/

- Razorpay Webstore Branding:
  https://razorpay.com/docs/payments/webstore/faqs/

- Razorpay Payment Button Themes:
  https://razorpay.com/docs/payments/payment-button/custom/

These references should be checked again before finalizing any public-facing branding, because the Razorpay design system can evolve.

---

# 128. Final Implementation Priority

Do not spend three days polishing animation before the product works.

Build in this order:

```text
1. Layout
2. Navigation
3. Design tokens
4. Core components
5. Dashboard
6. Catalogue
7. Simulation
8. Optimization
9. Transaction UI
10. Audit
11. Responsive
12. Animation polish
13. Final visual QA
```

The product must be functional before it becomes beautiful.

---

# 129. Final Rule

```text
Razorpay in identity.
AI in interaction.
Fintech in trust.
Data in hierarchy.
Motion in state.
Nothing decorative without purpose.
```


## September 4 UX/Terminology Audit
- **"X products passed filters"**: The frontend funnel display may show truncated subset counts (e.g., 30 products) instead of the full evaluated 2,977 catalogue. The terminology should reflect "Displayed Products" rather than "Products Evaluated".
- **"What-If Match Rate"**: This is a catalogue-level evaluation, mathematically accurate given the full active catalogue scope, but overriding one product out of 2,977 may show very small deltas.