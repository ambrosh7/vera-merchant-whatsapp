export type NavItem = {
  id: string
  label: string
  icon: 'hub' | 'inbox' | 'store' | 'campaign' | 'insights'
  badge?: number
}

export type ScoreDimension = {
  label: string
  score: number
  max: number
}

export type Message =
  | {
      id: string
      kind: 'vera'
      time: string
      label: string
      body: string
      highlight?: string
      source?: string
      contexts: { label: string; tone: 'neutral' | 'merchant' | 'trigger' | 'disabled' }[]
    }
  | {
      id: string
      kind: 'merchant'
      time: string
      author: string
      body: string
    }
  | {
      id: string
      kind: 'draft'
      time: string
      body: string
      recipients: number
      attachment: {
        title: string
        summary: string
        offer: string
        sku: string
      }
    }

export const navItems: NavItem[] = [
  { id: 'studio', label: 'Studio', icon: 'hub' },
  { id: 'inbox', label: 'Inbox', icon: 'inbox', badge: 12 },
  { id: 'merchants', label: 'Merchants', icon: 'store' },
  { id: 'campaigns', label: 'Campaigns', icon: 'campaign' },
  { id: 'insights', label: 'Insights', icon: 'insights' },
]

export const qualityScores: ScoreDimension[] = [
  { label: 'Specificity', score: 10, max: 10 },
  { label: 'Category fit', score: 10, max: 10 },
  { label: 'Merchant fit', score: 10, max: 10 },
  { label: 'Trigger', score: 10, max: 10 },
  { label: 'Compulsion', score: 9, max: 10 },
]

export const messages: Message[] = [
  {
    id: 'm1',
    kind: 'vera',
    time: '10:42 AM',
    label: 'Automated Clinical Dispatch',
    body: "Dr. Meera, JIDA's Oct issue landed. One item relevant to your high-risk adult patients — ",
    highlight:
      '2,100-patient trial showed 3-month fluoride recall cuts caries recurrence 38% better than 6-month.',
    source: 'source JIDA Oct 2026 p.14 · send_as Vera',
    contexts: [
      { label: 'Category: Dentists', tone: 'neutral' },
      { label: 'Merchant: Dr. Meera', tone: 'merchant' },
      { label: 'Trigger: jida_oct_caries', tone: 'trigger' },
      { label: 'Customer: unassigned', tone: 'disabled' },
    ],
  },
  {
    id: 'm2',
    kind: 'merchant',
    time: '10:44 AM',
    author: 'Dr. Meera Khurana · Mobile · Delivered via WhatsApp',
    body: 'Send me the abstract first — keep it short.',
  },
  {
    id: 'm3',
    kind: 'draft',
    time: '10:45 AM',
    body: "Got it. 5-line abstract + one CTA for your high-risk roster (124 adults). Approve and I'll queue it on WhatsApp:",
    recipients: 124,
    attachment: {
      title: 'Clinical Abstract Summary · JIDA 2026-OCT-14',
      summary:
        '“Quarterly topical fluoride varnish combined with 90-day recall regimens reduced interproximal decay rates by 38.4% (p < 0.001) in adults with existing restorations relative to bi-annual protocols.”',
      offer: 'Fluoride Varnish @ ₹199',
      sku: 'DEN-FLU-199',
    },
  },
]

export const actionQueue = [
  {
    id: 'q1',
    time: 'Today 11:10',
    title: 'Research Digest JIDA',
    detail: 'High-risk adult caries reduction abstract',
    status: 'DRAFT' as const,
    active: true,
  },
  {
    id: 'q2',
    time: 'Tomorrow 09:30',
    title: 'GBP Listing Remediation',
    detail: 'Clinic hours incomplete for Diwali week',
    status: 'ALERT' as const,
    active: false,
  },
  {
    id: 'q3',
    time: 'Fri 18:00',
    title: 'Patient Recall: Priya S.',
    detail: 'Automated on behalf of merchant',
    status: 'RECALL' as const,
    active: false,
  },
]

export const whyNow = {
  kind: 'research_digest',
  reason:
    "New clinical digest directly matches Dr. Meera's cohort of 124 adults overdue for preventive checkups.",
  window: 'Today 11:00 – 13:00 IST',
  confidence: 92,
}

export const contexts = {
  category: {
    title: 'Category: Dentists',
    voice: 'peer clinician, evidence-led, no commercial overclaim.',
    offers: ['Cleaning @ ₹299', 'Fluoride @ ₹199', 'Scaling @ ₹799'],
    digest: 'Indexed digest: JIDA Oct 2026',
  },
  merchant: {
    title: "Dr. Meera's Dental Clinic",
    locality: 'Lajpat Nagar II, New Delhi · Pin 110024',
    ctr: '2.1%',
    peerCtr: '3.0%',
    roster: '124 high-risk',
    alert: 'GBP hours incomplete for Diwali',
  },
  trigger: {
    id: 'research_digest_jida_oct',
    kind: 'research_digest',
    why: 'New peer-reviewed caries paper strictly matches patient cohort profile',
    action:
      'Send digest abstract + offer patient education broadcast via clinic notes WhatsApp.',
  },
  versions: 'category v2 · merchant v5 · trigger v1',
}
