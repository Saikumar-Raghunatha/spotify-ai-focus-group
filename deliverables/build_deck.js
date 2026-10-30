// Build the presentation from results.json.  node deck.js <results.json> <out.pptx>
const pptxgen = require("pptxgenjs");
const fs = require("fs");
const path = require("path");
const { applyTheme } = require("/Users/medha/.claude/skills/synced/835c2590-8b5c-4992-b446-21ddb94f4d7e_741b6426-ea7e-451a-82f9-befa987702ef/pptx/scripts/apply_theme.js");

const R = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const OUT = process.argv[3];
const E23 = R.events["2023"], E26 = R.events["2026"];
const ICON = (n, t) => path.join(__dirname, "icons", `${n}_${t}.png`);
const pct = (x) => `${Math.round(x * 100)}%`;

const THEME = {
  name: "Synthetic Focus Group", headFontFace: "Cambria", bodyFontFace: "Calibri",
  colors: { dk1: "16302A", lt1: "FFFFFF", dk2: "0B1F1A", lt2: "EEF5F1", accent1: "0E9F5A", accent2: "E8553F",
            accent3: "F2B33D", accent4: "8FB9A8", accent5: "3D5A80", accent6: "5B6B66", hlink: "0E9F5A", folHlink: "3D5A80" },
};
const HEX = THEME.colors;   // hex-only options (chart colors, shadows, grid lines)

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";                       // 13.33 x 7.5 in
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "Can an AI focus group predict a price-hike backlash?";
pres.subject = "Synthetic personas vs the real r/spotify reaction to the 2023 and 2026 US price increases";
const C = pres.SchemeColor;

const FOOT = "AI focus group  ·  Spotify US price increases 2023 / 2026";
pres.defineSlideMaster({
  title: "TITLE", background: { color: C.text2 },
  objects: [{ placeholder: { options: { name: "title", type: "title", x: 0.7, y: 1.75, w: 7.2, h: 2.2, fontFace: THEME.headFontFace,
              fontSize: 40, bold: true, color: C.background1, valign: "top", align: "left", margin: 0 }, text: "" } },
            { placeholder: { options: { name: "body", type: "body", x: 0.7, y: 4.05, w: 7.0, h: 0.9, fontSize: 18,
              color: C.accent4, valign: "top", margin: 0 }, text: "" } }],
});
pres.defineSlideMaster({
  title: "CONTENT", background: { color: C.background1 },
  objects: [{ placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.38, w: 12.1, h: 0.8, fontFace: THEME.headFontFace,
              fontSize: 32, bold: true, color: C.text1, valign: "middle", align: "left", margin: 0 }, text: "" } },
            { text: { text: FOOT, options: { x: 0.6, y: 7.0, w: 8, h: 0.3, fontSize: 10, color: C.accent6, margin: 0 } } }],
  slideNumber: { x: 12.3, y: 7.0, w: 0.5, h: 0.3, fontSize: 10, color: C.accent6, align: "right" },
});
pres.defineSlideMaster({
  title: "DARK", background: { color: C.text2 },
  objects: [{ placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.38, w: 12.1, h: 0.8, fontFace: THEME.headFontFace,
              fontSize: 32, bold: true, color: C.background1, valign: "middle", align: "left", margin: 0 }, text: "" } },
            { text: { text: FOOT, options: { x: 0.6, y: 7.0, w: 8, h: 0.3, fontSize: 10, color: C.accent4, margin: 0 } } }],
  slideNumber: { x: 12.3, y: 7.0, w: 0.5, h: 0.3, fontSize: 10, color: C.accent4, align: "right" },
});

const shadow = () => ({ type: "outer", color: "000000", opacity: 0.12, blur: 8, offset: 2, angle: 90 });
function card(s, x, y, w, h, fill, name, withShadow = true) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: fill }, line: { color: fill },
    rectRadius: 0.12, shadow: withShadow ? shadow() : undefined, objectName: name });
}
function iconDot(s, icon, tone, x, y, d, fill, name) {
  s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: fill }, line: { color: fill }, objectName: name + " circle" });
  const p = d * 0.25;
  s.addImage({ path: ICON(icon, tone), x: x + p, y: y + p, w: d - 2 * p, h: d - 2 * p, objectName: name + " icon" });
}
function txt(s, text, o) { s.addText(text, { isTextBox: true, margin: 0, valign: "top", ...o }); }

// ---------- Slide 0: title ----------
pres.addSection({ title: "Introduction" });
{
  const s = pres.addSlide({ masterName: "TITLE", sectionTitle: "Introduction" });
  txt(s, "MSBA ANALYTICS PROJECT  ·  SYNTHETIC CONSUMER RESEARCH", { x: 0.7, y: 1.1, w: 7.5, h: 0.35, fontSize: 12,
      bold: true, color: C.accent1, charSpacing: 2, objectName: "Kicker" });
  s.addText("Can an AI focus group predict a price-hike backlash?", { placeholder: "title" });
  s.addText("Simulating the r/spotify community before Spotify's 2023 and 2026 US price increases", { placeholder: "body" });
  txt(s, "[Team member names]   ·   [Course]   ·   [Date]", { x: 0.7, y: 5.75, w: 7.2, h: 0.4, fontSize: 14,
      color: C.background1, objectName: "Team line" });
  // price staircase: US Premium Individual
  const steps = [["2011", 9.99, false, ""], ["Jul 2023", 10.99, true, "back-test"], ["Jun 2024", 11.99, false, ""],
                 ["Jan 2026", 12.99, true, "holdout"]];
  const base = 6.0, x0 = 8.55, bw = 0.9, gap = 0.22;
  txt(s, "US Premium Individual, per month", { x: x0, y: 1.2, w: 4.4, h: 0.3, fontSize: 12, color: C.accent4, objectName: "Ladder caption" });
  steps.forEach(([yr, price, tested, tag], i) => {
    const h = (price - 7.5) * 0.72, x = x0 + i * (bw + gap), y = base - h;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: bw, h, rectRadius: 0.08, fill: { color: tested ? C.accent1 : C.accent4,
      transparency: tested ? 0 : 55 }, line: { color: tested ? C.accent1 : C.accent4, transparency: tested ? 0 : 55 },
      objectName: `Price bar ${yr}` });
    txt(s, `$${price}`, { x: x - 0.1, y: y - 0.42, w: bw + 0.2, h: 0.35, fontSize: 16, bold: true, align: "center",
        color: C.background1, objectName: `Price ${yr}` });
    txt(s, yr, { x: x - 0.15, y: base + 0.1, w: bw + 0.3, h: 0.3, fontSize: 12, align: "center", color: C.accent4, objectName: `Year ${yr}` });
    if (tag) txt(s, tag, { x: x - 0.1, y: base + 0.4, w: bw + 0.2, h: 0.3, fontSize: 11, bold: true, align: "center",
        color: C.accent3, objectName: `Tag ${yr}` });
  });
  s.addNotes("Our question: if you build an AI 'focus group' only from what Spotify users wrote BEFORE a price increase, " +
    "does it react the way the real community did AFTER? We test it twice: the July 2023 hike (first US increase since 2011, " +
    "our tuning event) and the January 2026 hike (a one-shot holdout run with everything frozen).");
}

// ---------- Slide 1: problem & motivation ----------
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Introduction" });
  s.addText("Price hikes are high-stakes and hard to pre-test", { placeholder: "title" });
  const rows = [
    ["tags", "Small change, huge base", "Three US increases in 30 months: $10.99 → $12.99 for Individual, +$2 for Duo and Family in 2026."],
    ["survey", "Classic research is slow", "Surveys and focus groups take weeks, cost money, and capture what people say they'll do."],
    ["robot", "AI 'synthetic customers' are cheap", "But do they react like your actual customers, or like a generic internet crowd?"],
  ];
  rows.forEach(([ic, head, body], i) => {
    const y = 1.6 + i * 1.6;
    iconDot(s, ic, "w", 0.6, y, 0.85, C.accent1, `Reason ${i + 1}`);
    txt(s, head, { x: 1.7, y: y - 0.02, w: 5.4, h: 0.4, fontSize: 20, bold: true, color: C.text1, objectName: `Reason ${i + 1} head` });
    txt(s, body, { x: 1.7, y: y + 0.42, w: 5.4, h: 0.85, fontSize: 15, color: C.accent6, objectName: `Reason ${i + 1} body` });
  });
  card(s, 7.6, 1.5, 5.1, 4.9, C.text2, "Question card");
  txt(s, "RESEARCH QUESTION", { x: 8.0, y: 1.85, w: 4.4, h: 0.3, fontSize: 12, bold: true, color: C.accent1, charSpacing: 2, objectName: "RQ kicker" });
  txt(s, "Can AI personas built only from posts written before an announcement reproduce how the community actually reacted?",
      { x: 8.0, y: 2.25, w: 4.4, h: 2.0, fontSize: 20, fontFace: THEME.headFontFace, color: C.background1, objectName: "RQ text" });
  const chips = [["Jul 2023 hike", "stock −5% that morning"], ["Jan 2026 hike", "stock +3% premarket"]];
  chips.forEach(([a, b], i) => {
    const x = 8.0 + i * 2.25;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 4.75, w: 2.1, h: 1.2, rectRadius: 0.1, fill: { color: C.background1, transparency: 88 },
      line: { color: C.accent4, transparency: 50 }, objectName: `Market chip ${i + 1}` });
    txt(s, a, { x: x + 0.15, y: 4.88, w: 1.8, h: 0.3, fontSize: 12, bold: true, color: C.accent3, objectName: `Chip ${i + 1} head` });
    txt(s, b, { x: x + 0.15, y: 5.2, w: 1.8, h: 0.6, fontSize: 14, color: C.background1, objectName: `Chip ${i + 1} body` });
  });
  s.addNotes("Why it matters: Spotify raised the US Individual price three times in 30 months. Markets read the reaction " +
    "differently each time (down ~5% the morning of the 2023 hike, up ~3% premarket in 2026). Pricing teams want to know before " +
    "launch who will complain, who will cancel and where they will go. LLM personas promise answers in minutes, but the open " +
    "question is whether they reflect the real customer base. We test that against what actually happened.");
}

// ---------- Slide 2: data ----------
pres.addSection({ title: "Data" });
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Data" });
  s.addText("Two price hikes, strict before-and-after windows", { placeholder: "title" });
  txt(s, "Reddit r/spotify + r/truespotify via the Arctic Shift archive  ·  usernames replaced by hashes",
      { x: 0.6, y: 1.2, w: 12, h: 0.35, fontSize: 14, color: C.accent6, objectName: "Source line" });
  const lanes = [
    { y: 1.95, ev: "July 2023", pre: "Jul 2022 – 20 Jul 2023", gap: "WSJ leak 21 Jul", post: "24 Jul – 7 Aug",
      n1: "202,676", l1: "pre-event posts & comments", n2: "22,352", l2: "rows feed the personas", n3: "1,345", l3: "reaction rows labeled" },
    { y: 4.35, ev: "January 2026", pre: "Nov 2024 – 23 Nov 2025", gap: "FT report 25 Nov", post: "15 – 29 Jan",
      n1: "487,944", l1: "pre-event posts & comments", n2: "20,864", l2: "rows feed the personas", n3: "895", l3: "reaction rows labeled" },
  ];
  lanes.forEach((L, i) => {
    txt(s, L.ev, { x: 0.6, y: L.y, w: 2.2, h: 0.4, fontSize: 18, bold: true, color: C.text1, objectName: `Lane ${i + 1} name` });
    const bx = 2.9, by = L.y;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: bx, y: by, w: 5.6, h: 0.5, rectRadius: 0.08, fill: { color: C.accent1 }, line: { color: C.accent1 }, objectName: `Lane ${i + 1} pre` });
    txt(s, `Persona window  ·  ${L.pre}`, { x: bx + 0.15, y: by + 0.1, w: 5.3, h: 0.3, fontSize: 13, bold: true, color: C.background1, objectName: `Lane ${i + 1} pre text` });
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 8.6, y: by, w: 1.65, h: 0.5, rectRadius: 0.08, fill: { color: C.background2 }, line: { color: C.accent4 }, objectName: `Lane ${i + 1} gap` });
    txt(s, "excluded", { x: 8.6, y: by + 0.1, w: 1.65, h: 0.3, fontSize: 12, align: "center", color: C.accent6, objectName: `Lane ${i + 1} gap text` });
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 10.35, y: by, w: 2.35, h: 0.5, rectRadius: 0.08, fill: { color: C.accent2 }, line: { color: C.accent2 }, objectName: `Lane ${i + 1} post` });
    txt(s, `Reaction · ${L.post}`, { x: 10.45, y: by + 0.1, w: 2.2, h: 0.3, fontSize: 13, bold: true, color: C.background1, objectName: `Lane ${i + 1} post text` });
    txt(s, L.gap, { x: 8.45, y: by + 0.55, w: 1.95, h: 0.3, fontSize: 11, align: "center", color: C.accent6, italic: true, objectName: `Lane ${i + 1} leak` });
    [[L.n1, L.l1], [L.n2, L.l2], [L.n3, L.l3]].forEach(([n, l], j) => {
      const x = 2.9 + j * 3.3;
      txt(s, n, { x, y: by + 0.95, w: 3.1, h: 0.6, fontSize: 30, bold: true, fontFace: THEME.headFontFace, color: j === 2 ? C.accent2 : C.text1, objectName: `Lane ${i + 1} stat ${j + 1}` });
      txt(s, l, { x, y: by + 1.55, w: 3.1, h: 0.35, fontSize: 13, color: C.accent6, objectName: `Lane ${i + 1} stat ${j + 1} label` });
    });
  });
  s.addNotes("Leakage control is the backbone of the design. Personas only ever see posts written before the news leaked " +
    "(WSJ on 21 Jul 2023; Financial Times on ~25 Nov 2025), so they cannot have read about the hike. The days between the leak " +
    "and the official announcement are dropped from both sides. Ground truth is the first two weeks after the official " +
    "announcement, when most of the reaction happens. 2026 data was pulled separately and kept sealed until 2023 was frozen.");
}

// ---------- Slide 3: pre-processing ----------
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Data" });
  s.addText("From raw threads to six community segments", { placeholder: "title" });
  const steps = [["broom", "Clean", "dedupe, drop bots, ≥15 words"], ["lock", "Cut for leakage", "stop before the news leaks"],
                 ["filter", "Focus & sample", "27,686 posts / year, 9.4% on price"], ["vector", "Embed", "MiniLM sentence vectors"],
                 ["layers", "Segment", "k-means, k = 6"]];
  steps.forEach(([ic, h, b], i) => {
    const x = 0.6 + i * 2.5;
    card(s, x, 1.4, 2.25, 1.75, C.background2, `Step ${i + 1} card`, false);
    iconDot(s, ic, "w", x + 0.2, 1.6, 0.6, C.accent1, `Step ${i + 1}`);
    txt(s, h, { x: x + 0.2, y: 2.3, w: 1.95, h: 0.35, fontSize: 16, bold: true, color: C.text1, objectName: `Step ${i + 1} head` });
    txt(s, b, { x: x + 0.2, y: 2.65, w: 1.95, h: 0.45, fontSize: 12, color: C.accent6, objectName: `Step ${i + 1} body` });
    if (i < steps.length - 1) txt(s, "›", { x: x + 2.24, y: 1.95, w: 0.28, h: 0.5, fontSize: 24, bold: true, align: "center", color: C.accent1, objectName: `Arrow ${i + 1}` });
  });
  const order = ["5", "2", "4", "0", "1", "3"];
  const names = order.map((k) => R.segments[k].name.replace(" (not simulated)", "*"));
  s.addChart(pres.charts.BAR, [
    { name: "2023", labels: names, values: order.map((k) => R.segments[k].share_2023) },
    { name: "2026", labels: names, values: order.map((k) => R.segments[k].share_2026) },
  ], { x: 0.5, y: 3.45, w: 7.9, h: 3.45, barDir: "bar", barGrouping: "clustered", barGapWidthPct: 60,
       chartColors: [HEX.accent4, HEX.accent1], catAxisOrientation: "maxMin",
       showValue: true, dataLabelFormatCode: "0%", dataLabelFontSize: 10, dataLabelColor: HEX.accent6, dataLabelFontFace: "+mn-lt",
       catAxisLabelFontSize: 12, catAxisLabelColor: HEX.dk1, catAxisLabelFontFace: "+mn-lt", valAxisHidden: true,
       valGridLine: { style: "none" }, catGridLine: { style: "none" },
       showLegend: true, legendPos: "t", legendFontSize: 11, legendFontFace: "+mn-lt", legendColor: HEX.accent6,
       showTitle: true, title: "Share of sampled posts by segment", titleFontSize: 13, titleColor: HEX.dk1, titleFontFace: "+mn-lt",
       objectName: "Segment share chart" });
  card(s, 8.8, 3.6, 3.9, 3.1, C.text2, "Segment insight card");
  txt(s, "WHAT CHANGED", { x: 9.1, y: 3.85, w: 3.4, h: 0.3, fontSize: 12, bold: true, color: C.accent1, charSpacing: 2, objectName: "Insight kicker" });
  txt(s, [{ text: "UI backlash faded", options: { bold: true, breakLine: true } },
          { text: `UI-update resisters ${pct(R.segments["0"].share_2023)} → ${pct(R.segments["0"].share_2026)}`, options: { breakLine: true } },
          { text: " ", options: { breakLine: true, fontSize: 8 } },
          { text: "Price and value talk grew", options: { bold: true, breakLine: true } },
          { text: `Premium value judges ${pct(R.segments["1"].share_2023)} → ${pct(R.segments["1"].share_2026)}` }],
      { x: 9.1, y: 4.25, w: 3.4, h: 1.7, fontSize: 15, color: C.background1, objectName: "Insight text" });
  txt(s, "*Genre talk is not simulated. 2026 posts join the frozen 2023 segments.", { x: 9.1, y: 6.0, w: 3.4, h: 0.6, fontSize: 11, color: C.accent4, objectName: "Insight note" });
  s.addNotes("Pre-processing reuses one pipeline for both years. We clean and de-duplicate, hash usernames, cut at the leak date, " +
    "keep posts about pricing, plans, alternatives, quality, artists or features, and sample evenly across months with price " +
    "talk boosted to 9.4%. Sentence embeddings (all-MiniLM-L6-v2) go into k-means; k = 6 had the best silhouette in 6-8. " +
    "For the 2026 holdout we did NOT re-cluster: each 2026 post joins its nearest 2023 segment, so no one had to read holdout " +
    "data to name clusters. The genre/artist-talk segment is dropped from simulation because it rarely discusses the product.");
}

// ---------- Slide 4: personas ----------
pres.addSection({ title: "Analytics" });
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Analytics" });
  s.addText("28 personas, each speaking from real posts", { placeholder: "title" });
  const segs = [["Premium value judges", 7, 1], ["Disillusioned comparers", 7, 1], ["UI-update resisters", 5, 0],
                ["Library power users", 5, 0], ["Podcast-flooded listeners", 2, 0]];
  txt(s, "Personas per segment", { x: 0.6, y: 1.35, w: 6, h: 0.35, fontSize: 14, bold: true, color: C.accent6, objectName: "Seg list head" });
  segs.forEach(([name, n, sat], i) => {
    const y = 1.85 + i * 0.78;
    txt(s, name, { x: 0.6, y: y + 0.05, w: 3.0, h: 0.35, fontSize: 15, color: C.text1, objectName: `Seg ${i + 1} name` });
    for (let k = 0; k < n + sat; k++) {
      const isSat = k >= n;
      s.addShape(pres.shapes.OVAL, { x: 3.7 + k * 0.38, y: y + 0.07, w: 0.3, h: 0.3, fill: { color: isSat ? C.accent3 : C.accent1 },
        line: { color: isSat ? C.accent3 : C.accent1 }, objectName: `Seg ${i + 1} dot ${k + 1}` });
    }
  });
  s.addShape(pres.shapes.OVAL, { x: 0.6, y: 5.95, w: 0.22, h: 0.22, fill: { color: C.accent1 }, line: { color: C.accent1 }, objectName: "Legend dot 1" });
  txt(s, "keyword archetypes + k-means sub-types", { x: 0.9, y: 5.9, w: 3.5, h: 0.3, fontSize: 12, color: C.accent6, objectName: "Legend 1" });
  s.addShape(pres.shapes.OVAL, { x: 4.4, y: 5.95, w: 0.22, h: 0.22, fill: { color: C.accent3 }, line: { color: C.accent3 }, objectName: "Legend dot 2" });
  txt(s, "satisfied subscriber (tuning round)", { x: 4.7, y: 5.9, w: 3, h: 0.3, fontSize: 12, color: C.accent6, objectName: "Legend 2" });
  txt(s, "Each persona's posts are its own: no post is shared, and it can only search its own history.",
      { x: 0.6, y: 6.35, w: 7, h: 0.4, fontSize: 13, italic: true, color: C.accent6, objectName: "Pool note" });
  // persona card
  const P = E23.personas.find((p) => p.id === "s1_p1");
  card(s, 7.9, 1.35, 4.85, 5.4, C.background1, "Persona card");
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 7.9, y: 1.35, w: 4.85, h: 5.4, rectRadius: 0.12, fill: { type: "none" },
    line: { color: C.accent4, width: 1 }, objectName: "Persona card outline" });
  iconDot(s, "user", "w", 8.2, 1.6, 0.75, C.accent1, "Persona avatar");
  txt(s, `${P.name}, 2023 persona`, { x: 9.1, y: 1.62, w: 3.5, h: 0.4, fontSize: 18, bold: true, color: C.text1, objectName: "Persona name" });
  txt(s, "Student plan · price-sensitive", { x: 9.1, y: 2.02, w: 3.5, h: 0.3, fontSize: 13, color: C.accent1, objectName: "Persona label" });
  txt(s, [{ text: "Why I stay  ", options: { bold: true, color: C.text1 } },
          { text: "the student price, the Hulu bundle, offline downloads for my commute" }],
      { x: 8.2, y: 2.6, w: 4.3, h: 0.9, fontSize: 14, color: C.accent6, objectName: "Persona stay" });
  txt(s, [{ text: "Pain points  ", options: { bold: true, color: C.text1 } },
          { text: "Showtime dropped from the bundle, confusing student verification" }],
      { x: 8.2, y: 3.5, w: 4.3, h: 0.9, fontSize: 14, color: C.accent6, objectName: "Persona pain" });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 8.2, y: 4.5, w: 4.25, h: 1.7, rectRadius: 0.1, fill: { color: C.background2 },
    line: { color: C.background2 }, objectName: "Reaction bubble" });
  txt(s, "Her simulated reaction to the 2023 hike", { x: 8.4, y: 4.6, w: 3.9, h: 0.3, fontSize: 11, bold: true, color: C.accent1, objectName: "Reaction kicker" });
  txt(s, "“The student plan going up a dollar sucks... the Hulu bundle still makes it a steal so I will probably stay.”",
      { x: 8.4, y: 4.92, w: 3.9, h: 1.2, fontSize: 14, italic: true, color: C.text1, objectName: "Reaction quote" });
  txt(s, `Built from ${P.pool} of her own pre-2023 posts`, { x: 8.2, y: 6.3, w: 4.3, h: 0.3, fontSize: 11, color: C.accent6, objectName: "Persona pool" });
  s.addNotes("Within each segment, keyword archetypes (students, family/duo payers, Apple Music switchers, lossless seekers, " +
    "artist-pay critics) get their own persona; the rest of the segment is split by k-means into sub-types. Claude Haiku agents " +
    "read ~40 real posts per persona and write a profile: who they are, value for money, price sensitivity, reasons to stay, pain " +
    "points and voice. Each persona's posts sit in its own local vector index (MiniLM embeddings), so retrieval can only return " +
    "that persona's history. After the 2023 tuning round two segments gained a 'satisfied subscriber' persona: 28 in total.");
}

// ---------- Slide 5: simulation & evaluation design ----------
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Analytics" });
  s.addText("Three ways to ask, one fair yardstick", { placeholder: "title" });
  const conds = [["search", "Personas + retrieval", "Profile plus the 8 of its own posts closest to the announcement", C.accent1, "Our method"],
                 ["user", "Personas only", "Same profile, no posts: does retrieval add anything?", C.accent4, "Ablation"],
                 ["robot", "Plain prompt", "“Simulate 28 r/spotify users”, no data at all", C.accent2, "Baseline"]];
  conds.forEach(([ic, h, b, col, tag], i) => {
    const x = 0.6 + i * 4.1;
    card(s, x, 1.35, 3.85, 2.05, C.background2, `Condition ${i + 1} card`, false);
    iconDot(s, ic, "w", x + 0.25, 1.6, 0.7, col, `Condition ${i + 1}`);
    txt(s, tag.toUpperCase(), { x: x + 1.1, y: 1.62, w: 2.6, h: 0.3, fontSize: 11, bold: true, color: col === C.accent4 ? C.accent6 : col, charSpacing: 2, objectName: `Condition ${i + 1} tag` });
    txt(s, h, { x: x + 1.1, y: 1.92, w: 2.6, h: 0.4, fontSize: 17, bold: true, color: C.text1, objectName: `Condition ${i + 1} head` });
    txt(s, b, { x: x + 0.25, y: 2.5, w: 3.4, h: 0.75, fontSize: 13, color: C.accent6, objectName: `Condition ${i + 1} body` });
  });
  txt(s, "5 repetitions each, persona order reshuffled  ·  every answer: comment, sentiment, action, themes", { x: 0.6, y: 3.55,
      w: 12.1, h: 0.35, fontSize: 13, color: C.accent6, align: "center", objectName: "Reps line" });
  const proto = [["Build on 2023", C.accent5], ["Tune once", C.accent3], ["Freeze everything", C.text1], ["Run 2026 once", C.accent2]];
  proto.forEach(([t, col], i) => {
    s.addShape(pres.shapes.CHEVRON, { x: 0.6 + i * 3.05, y: 4.15, w: 3.0, h: 0.6, fill: { color: col }, line: { color: col }, objectName: `Protocol ${i + 1}` });
    txt(s, t, { x: 0.95 + i * 3.05, y: 4.27, w: 2.35, h: 0.35, fontSize: 14, bold: true, align: "center", color: C.background1, objectName: `Protocol ${i + 1} text` });
  });
  const ev = [["comments", "Same labels for real posts", "6 actions · 4 sentiments · 12 themes, fixed before seeing the reaction. Haiku labeler; ≈97% agreement on a 100-row audit."],
              ["scale", "Distance, not anecdotes", "Total variation distance on actions and sentiment, theme rank correlation, and the share who say they'll leave."],
              ["target", "A realistic bar", "Real data split in half differs by ≈0.06-0.07: the best any simulation can hope for."]];
  ev.forEach(([ic, h, b], i) => {
    const x = 0.6 + i * 4.1;
    iconDot(s, ic, "g", x, 5.1, 0.55, C.background2, `Eval ${i + 1}`);
    txt(s, h, { x: x + 0.7, y: 5.1, w: 3.3, h: 0.35, fontSize: 15, bold: true, color: C.text1, objectName: `Eval ${i + 1} head` });
    txt(s, b, { x: x + 0.7, y: 5.47, w: 3.3, h: 1.3, fontSize: 12, color: C.accent6, objectName: `Eval ${i + 1} body` });
  });
  s.addNotes("Every condition sees the same announcement text and answers in the same structured format. The plain prompt is " +
    "what most teams would try first. Real post-event comments are labeled with exactly the same scheme, chosen before looking " +
    "at the reaction; a second model audit of 100 labels agreed ~97% of the time. Total variation distance is half the sum of " +
    "absolute differences between two distributions (0 = identical). We allowed one tuning round on 2023, froze everything, and " +
    "ran 2026 a single time.");
}

// ---------- Slide 6: 2023 results ----------
pres.addSection({ title: "Results" });
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Results" });
  s.addText("2023: personas track real actions, plain AI doesn't", { placeholder: "title" });
  const A = ["cancel", "switch", "downgrade", "complain", "accept", "ignore"];
  const lab = A.map((a) => a[0].toUpperCase() + a.slice(1));
  s.addChart(pres.charts.BAR, [
    { name: "Real community", labels: lab, values: A.map((a) => E23.real.action[a]) },
    { name: "AI personas", labels: lab, values: A.map((a) => E23.conditions.rag.action[a]) },
    { name: "Plain prompt", labels: lab, values: A.map((a) => E23.conditions.plain.action[a]) },
  ], { x: 0.5, y: 1.3, w: 7.9, h: 5.5, barDir: "col", barGrouping: "clustered", barGapWidthPct: 70,
       chartColors: [HEX.dk1, HEX.accent1, HEX.accent2],
       showValue: true, dataLabelFormatCode: "0%", dataLabelFontSize: 10, dataLabelColor: HEX.accent6, dataLabelPosition: "outEnd", dataLabelFontFace: "+mn-lt",
       catAxisLabelFontSize: 13, catAxisLabelColor: HEX.dk1, catAxisLabelFontFace: "+mn-lt",
       valAxisHidden: true, valGridLine: { style: "none" }, catGridLine: { style: "none" },
       showLegend: true, legendPos: "t", legendFontSize: 12, legendFontFace: "+mn-lt", legendColor: HEX.dk1,
       showTitle: true, title: "What people say they'll do (July 2023)", titleFontSize: 14, titleColor: HEX.dk1, titleFontFace: "+mn-lt",
       objectName: "2023 action chart" });
  const stats = [
    [E23.conditions.rag.action_tvd.toFixed(2), "action distance", `plain prompt ${E23.conditions.plain.action_tvd.toFixed(2)}  ·  untuned ${E23.conditions.rag_untuned.action_tvd.toFixed(2)}`, C.accent1],
    [pct(E23.conditions.rag.leave), "say they'll leave", `real ${pct(E23.real.leave)}  ·  plain prompt ${pct(E23.conditions.plain.leave)}`, C.accent1],
    [E23.conditions.rag.theme_rho.toFixed(2), "theme rank match", `plain prompt ${E23.conditions.plain.theme_rho.toFixed(2)}`, C.accent1],
  ];
  stats.forEach(([n, l, sub, col], i) => {
    const y = 1.45 + i * 1.75;
    card(s, 8.85, y, 3.85, 1.5, C.background2, `Stat ${i + 1} card`, false);
    txt(s, n, { x: 9.1, y: y + 0.12, w: 1.9, h: 0.85, fontSize: 40, bold: true, fontFace: THEME.headFontFace, color: col, objectName: `Stat ${i + 1} number` });
    txt(s, l, { x: 10.95, y: y + 0.32, w: 1.7, h: 0.5, fontSize: 15, bold: true, color: C.text1, objectName: `Stat ${i + 1} label` });
    txt(s, sub, { x: 9.1, y: y + 1.0, w: 3.5, h: 0.35, fontSize: 12, color: C.accent6, objectName: `Stat ${i + 1} sub` });
  });
  s.addNotes(`July 2023, after the single tuning round. Real community (n = ${E23.real.n_opinion} opinionated comments from ` +
    `${E23.real.authors} authors): 12% say they'll cancel, switch or downgrade; most complain and stay or defend the price. ` +
    `The persona focus group lands at ${pct(E23.conditions.rag.leave)} leave intent and an action distance of ` +
    `${E23.conditions.rag.action_tvd.toFixed(2)}; the plain prompt imagines ${pct(E23.conditions.plain.leave)} leaving, about three ` +
    `times reality. The untuned personas scored ${E23.conditions.rag_untuned.action_tvd.toFixed(2)}: the tuning round mainly ` +
    `fixed missing defenders. Real-vs-real noise floor is about 0.06.`);
}

// ---------- Slide 7: holdout + a-ha ----------
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Results" });
  s.addText("2026 holdout and three a-ha moments", { placeholder: "title" });
  card(s, 0.6, 1.35, 5.9, 5.4, C.text2, "Holdout card");
  txt(s, "JANUARY 2026  ·  ONE SHOT, NOTHING RETUNED", { x: 0.95, y: 1.6, w: 5.3, h: 0.3, fontSize: 12, bold: true, color: C.accent1, charSpacing: 2, objectName: "Holdout kicker" });
  const c = E26.conditions;
  const head = { bold: true, color: C.accent4, fontSize: 12 };
  const rowsT = [
    [{ text: "", options: head }, { text: "Real", options: { ...head, align: "center" } }, { text: "AI personas", options: { ...head, align: "center" } }, { text: "Plain prompt", options: { ...head, align: "center" } }],
    ["Say they'll leave", pct(E26.real.leave), pct(c.rag.leave), pct(c.plain.leave)],
    ["Defend the price", pct(E26.real.action.accept), pct(c.rag.action.accept), pct(c.plain.action.accept)],
    ["Action distance", "0.07*", c.rag.action_tvd.toFixed(2), c.plain.action_tvd.toFixed(2)],
    ["Sentiment distance", "0.06*", c.rag.sentiment_tvd.toFixed(2), c.plain.sentiment_tvd.toFixed(2)],
  ].map((r, i) => i === 0 ? r : r.map((v, j) => ({ text: v, options: { color: j === 2 ? C.accent1 : C.background1, bold: j === 2,
       align: j === 0 ? "left" : "center", fontSize: 15 } })));
  s.addTable(rowsT, { x: 0.95, y: 2.1, w: 5.25, colW: [1.85, 0.95, 1.3, 1.15], rowH: 0.5, border: { type: "solid", pt: 0.5, color: HEX.accent6 },
    fill: { color: C.text2 }, fontFace: THEME.bodyFontFace, valign: "middle", objectName: "Holdout table" });
  txt(s, `Real leave intent doubled from ${pct(E23.real.leave)} (2023) to ${pct(E26.real.leave)} (2026). The personas moved with it (${pct(E23.conditions.rag.leave)} → ${pct(c.rag.leave)}); the plain prompt says 35\u201140% either way.`,
      { x: 0.95, y: 5.15, w: 5.3, h: 1.0, fontSize: 14, color: C.background1, objectName: "Holdout takeaway" });
  txt(s, "*real data vs itself: the best a simulation can reach", { x: 0.95, y: 6.25, w: 5.3, h: 0.3, fontSize: 11, color: C.accent4, objectName: "Floor note" });
  const aha = [
    ["smile", "Happy customers are quiet online", `Untuned personas found ${pct(E23.conditions.rag_untuned.action.accept)} defenders vs ${pct(E23.real.action.accept)} real. Giving reasons-to-stay equal weight lifted it to ${pct(E23.conditions.rag.action.accept)}.`],
    ["search", "Retrieval helps when history has signal", `No gain in 2023; in 2026 the personas' own posts about the 2024 hike cut the action distance from ${c.norag.action_tvd.toFixed(2)} to ${c.rag.action_tvd.toFixed(2)}.`],
    ["robot", "A generic LLM is not your customer", "The plain prompt plays a stereotyped 'internet reacts' crowd: churn talk 3x reality in 2023, plus piracy and can't-afford-it clichés."],
  ];
  aha.forEach(([ic, h, b], i) => {
    const y = 1.35 + i * 1.83;
    card(s, 6.85, y, 5.85, 1.62, C.background2, `Aha ${i + 1} card`, false);
    iconDot(s, ic, "w", 7.1, y + 0.25, 0.7, C.accent3, `Aha ${i + 1}`);
    txt(s, h, { x: 8.0, y: y + 0.2, w: 4.55, h: 0.4, fontSize: 17, bold: true, color: C.text1, objectName: `Aha ${i + 1} head` });
    txt(s, b, { x: 8.0, y: y + 0.62, w: 4.55, h: 0.95, fontSize: 13, color: C.accent6, objectName: `Aha ${i + 1} body` });
  });
  s.addNotes(`The holdout ran once with everything frozen. Real side: ${E26.real.n_opinion} opinionated reactions. Personas beat ` +
    `the plain prompt on actions (${c.rag.action_tvd.toFixed(2)} vs ${c.plain.action_tvd.toFixed(2)}) and sentiment ` +
    `(${c.rag.sentiment_tvd.toFixed(2)} vs ${c.plain.sentiment_tvd.toFixed(2)}, near the floor). Misses to admit: personas ` +
    `fixate on the Duo/Family $2 increase (plan cost in 54% of answers vs 11% real), still under-count defenders ` +
    `(${pct(c.rag.action.accept)} vs ${pct(E26.real.action.accept)}) and still bring up app complaints too often. The real ` +
    `community was primed by the November FT report; our personas were not.`);
}

// ---------- Slide 8: practical value ----------
pres.addSection({ title: "Application" });
{
  const s = pres.addSlide({ masterName: "DARK", sectionTitle: "Application" });
  s.addText("A pre-launch pulse check for pricing teams", { placeholder: "title" });
  const uses = [
    ["target", "Pre-test a price or plan change", "See which segments complain, accept or leave before the email goes out."],
    ["bullhorn", "Test the message", "Compare announcement wordings (e.g. 'benefit artists') against the same focus group."],
    ["route", "See where switchers go", "Apple Music, Tidal and YouTube Music came up in both years."],
    ["clock", "Minutes, not weeks", "~70 small Haiku agent runs for the whole study; rerun on new data any time."],
  ];
  uses.forEach(([ic, h, b], i) => {
    const x = 0.6 + (i % 2) * 6.15, y = 1.45 + Math.floor(i / 2) * 1.95;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: 5.95, h: 1.7, rectRadius: 0.12, fill: { color: C.background1, transparency: 92 },
      line: { color: C.accent4, transparency: 60 }, objectName: `Use ${i + 1} card` });
    iconDot(s, ic, "w", x + 0.3, y + 0.35, 0.8, C.accent1, `Use ${i + 1}`);
    txt(s, h, { x: x + 1.35, y: y + 0.3, w: 4.4, h: 0.4, fontSize: 18, bold: true, color: C.background1, objectName: `Use ${i + 1} head` });
    txt(s, b, { x: x + 1.35, y: y + 0.75, w: 4.4, h: 0.8, fontSize: 14, color: C.accent4, objectName: `Use ${i + 1} body` });
  });
  txt(s, [{ text: "Know the limits  ", options: { bold: true, color: C.accent3 } },
          { text: "Reddit posters are not all customers · personas still over-complain about the app and under-count defenders · one model family both labels and simulates." }],
      { x: 0.6, y: 5.55, w: 12.1, h: 0.7, fontSize: 14, color: C.background1, objectName: "Limits" });
  txt(s, "Use it as an early signal and a way to rank scenarios, not as a churn forecast.", { x: 0.6, y: 6.3, w: 12.1, h: 0.4,
      fontSize: 16, italic: true, fontFace: THEME.headFontFace, color: C.accent1, objectName: "Closing line" });
  s.addNotes("How a pricing or insights team would use this: before a change, run the frozen focus group on the draft " +
    "announcement and read the action mix by segment; compare wordings; watch which competitors come up. It is cheap enough to " +
    "rerun every time. It is not a churn forecast: it reflects people who post on Reddit, it leans negative, and the same model " +
    "family labels and simulates. Next steps: human-labeled ground truth, more segments (the genre-talk group), and more events.");
}

(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("wrote", OUT);
})();
