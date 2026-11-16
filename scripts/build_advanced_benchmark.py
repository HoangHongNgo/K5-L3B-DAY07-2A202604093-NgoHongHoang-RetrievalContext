"""Freeze hand-written WDR 2024 questions before running the advanced agent."""
import json
from pathlib import Path

from src.advanced import SOURCE_ID

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/advanced_questions.json"
rows = []


def add(split, group, question, expected, refs, reason=""):
    number = 1 + sum(r["split"] == split for r in rows)
    rows.append({"id": f"adv_{split}_{number:02d}", "split": split, "group": group,
                 "question": question, "answerable": bool(refs),
                 "expected_answer": expected if refs else None,
                 "expected_behavior": None if refs else "abstain",
                 "gold": [{"source_id": SOURCE_ID, "page": page, "region": region,
                           "evidence": evidence} for page, region, evidence in refs],
                 "reason": reason})


# Development set: 15 answerable questions, three per group, plus three absent.
add("dev", "table", "In Table P1.1, what share of global GDP belongs to lower-middle-income economies in 2022?", "8.3%", [(63,"Table P1.1; lower-middle-income row, global GDP column","8.3")])
add("dev", "table", "In Table P1.1, what share of global CO2 emissions belongs to high-income economies in 2022?", "35.2%", [(63,"Table P1.1; high-income row, CO2 column","35.2")])
add("dev", "table", "According to Table 2.1, which two strategies are higher priorities for lower-middle-income countries?", "Investment and infusion.", [(86,"Table 2.1; lower-middle-income row","Higher priority for investment and infusion")])
add("dev", "image_diagram", "In Figure 2.2, what is the middle stage labeled between 1i and 3i?", "2i: investment plus infusion.", [(88,"Figure 2.2, central stage","2i Investment + Infusion")])
add("dev", "image_diagram", "In Map 6.2, which broad continent has sparse electricity transmission lines compared with Europe?", "Africa.", [(182,"Map 6.2, world map","Sparse transmission lines across much of Africa")])
add("dev", "image_diagram", "In the left arrangement of Figure P2.1, which force has the largest circle?", "Preservation.", [(115,"Figure P2.1, left arrangement","Preservation is the largest circle")])
add("dev", "chart", "In Figure 3.5 panel a, what is the energy intensity of lower-middle-income countries?", "12.1 exajoules per trillion US dollars.", [(108,"Figure 3.5a, LMIC bar","12.1 exajoules/trillion US$")])
add("dev", "chart", "In Figure 3.2, did harmful semiconductor trade interventions rise or fall after 2019?", "They rose sharply.", [(105,"Figure 3.2b, harmful interventions","Harmful interventions skyrocketed since 2019")])
add("dev", "chart", "What two series are plotted in Figure 6.2's panels?", "Share of online job postings related to low-carbon technologies and share of listed firms mentioning them in shareholder meetings.", [(172,"Figure 6.2 panels a and b","Job postings and listed-firm shareholder meetings")])
add("dev", "multi_hop", "What CO2 emissions share does Table P1.1 report for upper-middle-income economies, and what carbon intensity does Figure 3.5 show for that income group?", "48.6% of global CO2 emissions; 0.086 GtCO2 equivalent per exajoule of energy consumption.", [(63,"Table P1.1, upper-middle-income CO2 column","48.6%"),(108,"Figure 3.5b, UMIC bar","0.086 GtCO2 equivalent/exajoule")])
add("dev", "multi_hop", "What does Table 2.1 prioritize for upper-middle-income countries, and how is that stage labeled in Figure 2.2?", "All three: investment, infusion, and innovation; the 3i stage.", [(86,"Table 2.1, upper-middle-income row","Three higher priorities"),(88,"Figure 2.2, right stage","3i Investment + Infusion + Innovation")])
add("dev", "multi_hop", "According to the 2022 jobs discussion, how many new job openings were related to low-carbon technologies, and what share-based measure appears in Figure 6.2 panel a?", "3.3 million new related job openings in 2022; Figure 6.2 tracks the share of online job postings mentioning low-carbon technologies.", [(171,"Text, low-carbon jobs paragraph","3.3 million new job openings"),(172,"Figure 6.2a","Share of job postings related to LCTs")])
add("dev", "text", "How many countries did the report classify as middle-income at the time of publication?", "108.", [(63,"Part 1 opening paragraph","108 countries")])
add("dev", "text", "What does the report mean by technology infusion in lower-middle-income countries?", "Importing modern technologies and business models and spreading them domestically at scale.", [(88,"Infuse first, then innovate","Importing and diffusing technology domestically")])
add("dev", "text", "What was the estimated record global fossil-fuel subsidy amount in 2022?", "US$1 trillion.", [(241,"Fossil-fuel subsidy paragraph","US$1 trillion")])
add("dev", "no_evidence", "What was the measured global fossil-fuel subsidy total in 2027?", None, [], "The 2024 report cannot contain a measured 2027 global total.")
add("dev", "no_evidence", "Who won the 2026 Nobel Prize in Economics according to this report?", None, [], "The prize is after the report's 2024 publication.")
add("dev", "no_evidence", "What exact share of global GDP did lower-middle-income countries have in 2035?", None, [], "2035 is beyond the report and no actual share is reported.")

# Held-out test set: 24 answerable questions with the required 6/5/5/4/4 grouping, plus six absent.
add("test", "table", "In Table P1.1, what percent of the world's people in extreme poverty lived in low-income economies in 2022?", "36.5%.", [(63,"Table P1.1; low-income row, extreme-poverty column","36.5")])
add("test", "table", "In Table P1.1, what share of 2022 global CO2 emissions came from upper-middle-income economies?", "48.6%.", [(63,"Table P1.1; upper-middle-income row, CO2 column","48.6")])
add("test", "table", "According to Table P1.1, what was high-income economies' share of global GDP in 2022?", "60.8%.", [(63,"Table P1.1; high-income row, GDP column","60.8")])
add("test", "table", "What share of global population was in lower-middle-income economies in Table P1.1?", "40.3%.", [(63,"Table P1.1; lower-middle-income row, population column","40.3")])
add("test", "table", "In Table 4.1, what is the listed downside of market power for lower-skilled workers under jobs?", "Their wages are depressed.", [(135,"Table 4.1; Jobs row, Cons column","Wages for lower-skilled workers are depressed")])
add("test", "table", "In Table 2.1, is innovation a higher or lower priority for upper-middle-income economies?", "Higher priority.", [(86,"Table 2.1; upper-middle-income row, innovation column","Higher priority")])
add("test", "image_diagram", "In Map 6.3, where are China's fossil-fuel jobs concentrated relative to low-carbon technology jobs?", "Fossil-fuel jobs cluster near coal mines, especially around Shanxi and western Guizhou; low-carbon jobs cluster on the southeast coast.", [(186,"Map 6.3 panels a and b","Coal regions versus southeast coast")])
add("test", "image_diagram", "In Map 6.1, which region shows the largest visible concentration of low-carbon job-posting bubbles?", "Europe.", [(173,"Map 6.1, Europe bubble cluster","Largest visible cluster in Europe")])
add("test", "image_diagram", "Which three levers feed into contestability in Figure 7.2?", "Institutions, incentives, and interventions.", [(195,"Figure 7.2, lower three boxes","Institutions, incentives, interventions")])
add("test", "image_diagram", "As economies move closer to the frontier in Figure 2.2, which contribution rises and which falls?", "Productivity rises; capital falls.", [(88,"Figure 2.2, two curves","Productivity rises and capital falls")])
add("test", "image_diagram", "In the right arrangement of Figure P2.1, how does preservation change compared with the left?", "Its circle becomes much smaller, while destruction becomes larger.", [(115,"Figure P2.1, left and right arrangements","Preservation shrinks and destruction grows")])
add("test", "chart", "In Figure 3.5 panel b, what is the carbon intensity of high-income countries' energy consumption?", "0.056 GtCO2 equivalent per exajoule.", [(108,"Figure 3.5b, HIC bar","0.056 GtCO2 equivalent/exajoule")])
add("test", "chart", "In Figure 7.1, how do the two fitted trends change as Italian firms become market leaders?", "Patents per 100 workers decrease while local politicians employed per 100 workers increase.", [(194,"Figure 7.1, fitted patent and politician lines","Patents down, politicians up toward market leader")])
add("test", "chart", "In Figure 3.1, which type of new trade policy is more numerous globally: helpful or harmful?", "Harmful policies.", [(104,"Figure 3.1, two series","Harmful policies outnumber helpful")])
add("test", "chart", "In Figure 6.1, what happens to the investment prices of solar PV and onshore wind over time?", "They decline substantially.", [(171,"Figure 6.1, solar and wind curves","Solar PV and onshore wind prices decline")])
add("test", "chart", "According to Figure 8.6, which indirect carbon-pricing instrument sends the strongest positive price signal?", "Energy taxes.", [(241,"Figure 8.6, energy taxes series","Energy taxes send strongest price signal")])
add("test", "multi_hop", "From Table P1.1, what is the combined CO2 emissions share of lower- and upper-middle-income economies in 2022?", "64.3% (15.7% + 48.6%).", [(63,"Table P1.1, CO2 column, two middle-income rows","15.7 + 48.6 = 64.3")])
add("test", "multi_hop", "From Table P1.1, what is the combined global GDP share of lower- and upper-middle-income economies?", "38.6% (8.3% + 30.3%).", [(63,"Table P1.1, GDP column, two middle-income rows","8.3 + 30.3 = 38.6")])
add("test", "multi_hop", "How does lower-middle-income energy intensity compare with high-income energy intensity in Figure 3.5, and what financing barrier does Figure 3.6 identify for middle-income solar projects?", "12.1 versus 5.1 exajoules per trillion US dollars (about 2.4 times); solar projects face a substantially higher weighted average cost of capital.", [(108,"Figure 3.5a, LMIC and HIC bars","12.1 and 5.1"),(109,"Figure 3.6 caption and plot","Higher weighted average cost of capital")])
add("test", "multi_hop", "What trend does Figure 6.1 show for low-carbon technology prices, and what trend does Figure 6.2 show for low-carbon technology job postings?", "Investment prices decline, while the share of related online job postings rises.", [(171,"Figure 6.1, investment price curves","Prices decline"),(172,"Figure 6.2a, job postings series","Job share rises")])
add("test", "text", "How many economies reached high-income status between 1990 and 2021 according to the report?", "34.", [(68,"Middle-income headwinds paragraph","34 economies")])
add("test", "text", "How many new online job openings were related to low-carbon technologies in 2022?", "3.3 million.", [(171,"Low-carbon jobs discussion","3.3 million")])
add("test", "text", "At least how many countries increased or reintroduced general fuel-price subsidies during the energy shock?", "At least 60.", [(241,"Energy-related measures paragraph","at least 60 countries")])
add("test", "text", "In Korea's 1950s school reform, approximately how did enrollment change in ten years?", "From about 40% to about 90%.", [(223,"Foundational skills and Korea paragraph","40 percent to 90 percent in 10 years")])
add("test", "no_evidence", "What was the actual 2030 global fossil-fuel subsidy total in US dollars?", None, [], "The document predates 2030; no actual 2030 total is available.")
add("test", "no_evidence", "Who won the 2027 Nobel Prize in Economics?", None, [], "The event is after the report's 2024 publication.")
add("test", "no_evidence", "What exact percentage of global GDP did upper-middle-income economies have in 2032?", None, [], "The report has 2022 values, not an actual 2032 value.")
add("test", "no_evidence", "What was the measured 2029 global average carbon tax per ton?", None, [], "2029 measured data are beyond the report's publication date.")
add("test", "no_evidence", "Which country had the most low-carbon job postings in 2031?", None, [], "The 2024 report cannot establish a 2031 observed ranking.")
add("test", "no_evidence", "How many countries became high-income between 2025 and 2035?", None, [], "The interval is beyond the report and no observed count is given.")

assert len(rows) == 48
# The first test was inspected and exposed citation/truncation failures; preserve
# it as a pilot, then replace all 30 test items with new held-out questions.
pilot = OUT.with_name("advanced_questions_pilot.json")
if not pilot.exists():
    pilot.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
rows = [r for r in rows if r["split"] == "dev"]

add("test", "table", "In Table P1.1, what was the 2022 global population share of low-income economies?", "8.9%.", [(63,"Table P1.1, low-income row, population column","8.9")])
add("test", "table", "In Table P1.1, what share of people in extreme poverty lived in lower-middle-income economies?", "55.4%.", [(63,"Table P1.1, lower-middle-income row, extreme-poverty column","55.4")])
add("test", "table", "In Table P1.1, what share of global GDP belonged to upper-middle-income economies?", "30.3%.", [(63,"Table P1.1, upper-middle-income row, GDP column","30.3")])
add("test", "table", "What share of the world's population was in high-income economies in Table P1.1?", "15.7%.", [(63,"Table P1.1, high-income row, population column","15.7")])
add("test", "table", "In Table 2.1, is innovation a higher or lower priority for lower-middle-income economies?", "Lower priority.", [(86,"Table 2.1, lower-middle-income row, innovation column","Lower priority")])
add("test", "table", "What consumer-welfare downside of market power is listed in Table 4.1?", "Cartels are easier to form when there are fewer players.", [(135,"Table 4.1, consumer welfare row, cons column","Easier to form cartels")])
add("test", "image_diagram", "What does the horizontal axis of Figure 2.2 represent?", "Proximity to the technology frontier.", [(88,"Figure 2.2, horizontal axis","Proximity to the frontier")])
add("test", "image_diagram", "Which force has the smallest circle in the left arrangement of Figure P2.1?", "Destruction.", [(115,"Figure P2.1, left arrangement","Destruction is smallest")])
add("test", "image_diagram", "What do the red lines in Map 6.2 represent?", "Electricity transmission lines.", [(182,"Map 6.2 legend","Power transmission lines")])
add("test", "image_diagram", "In Map 6.1's legend, which income group is colored orange?", "Upper-middle-income.", [(173,"Map 6.1, income-group legend","Upper-middle-income in orange")])
add("test", "image_diagram", "What is the top goal box in Figure 7.2 above contestability?", "Disciplining incumbency.", [(195,"Figure 7.2, top box","Disciplining incumbency")])
add("test", "chart", "What is the energy intensity of upper-middle-income economies in Figure 3.5 panel a?", "9.0 exajoules per trillion US dollars.", [(108,"Figure 3.5a, UMIC bar","9.0 exajoules/trillion US$")])
add("test", "chart", "What is the carbon intensity of lower-middle-income economies in Figure 3.5 panel b?", "0.098 GtCO2 equivalent per exajoule.", [(108,"Figure 3.5b, LMIC bar","0.098 GtCO2 equivalent/exajoule")])
add("test", "chart", "In Figure 3.4's 2028 projections, which interest-expense measure is larger: share of GDP or share of government revenues?", "Share of general government revenues: 9.7% versus 2.6% of GDP.", [(107,"Figure 3.4, 2028 endpoints","9.7% of revenues versus 2.6% of GDP")])
add("test", "chart", "In Figure 8.6, do energy subsidies send a positive or negative carbon-price signal?", "Negative; they undermine positive carbon-pricing signals.", [(241,"Figure 8.6, energy subsidies series","Negative price signal")])
add("test", "chart", "Which three fossil fuels dominate global primary energy consumption in 2022 in Figure 9.12?", "Coal, oil, and natural gas.", [(267,"Figure 9.12, 2022 stacked areas","Coal, oil, natural gas")])
add("test", "multi_hop", "What combined global GDP share do the two middle-income rows of Table P1.1 have, and what happened to their income per capita relative to the United States in Figure 1.2?", "38.6% of global GDP (8.3% + 30.3%); relative income per capita stayed broadly stagnant for decades.", [(63,"Table P1.1, GDP column, two middle-income rows","8.3 + 30.3 = 38.6"),(68,"Figure 1.2, trend","Stagnant relative income")])
add("test", "multi_hop", "What innovation downside appears in Table 4.1, and what happens to patents among Italian market leaders in Figure 7.1?", "Market power can reduce incentives to innovate and firm entry; market leaders have fewer patents per 100 workers as political connections rise.", [(135,"Table 4.1, innovation row, cons column","Fewer incentives to innovate"),(194,"Figure 7.1, patent trend","Patents decline among market leaders")])
add("test", "multi_hop", "What two barriers to renewable energy are illustrated by Map 6.2 and Figure 3.6?", "Sparse or outdated transmission networks and higher weighted average cost of capital for utility-scale solar projects in middle-income countries.", [(182,"Map 6.2, transmission networks","Sparse/outdated grids"),(109,"Figure 3.6, cost-of-capital plot","Higher WACC for middle-income solar")])
add("test", "multi_hop", "How do Figure 6.1 and Figure 9.1 together characterize solar panel costs and globalized value chains?", "Solar PV investment prices have fallen rapidly; globalized value chains lead to faster learning and lower global module prices than national scenarios.", [(171,"Figure 6.1, solar price curve","Rapid price declines"),(255,"Figure 9.1, global versus national scenarios","Globalized value chains lower prices")])
add("test", "text", "Approximately what share of the world's population lives in middle-income countries according to Part 1?", "About three-fourths.", [(63,"Part 1 opening paragraph","Three-fourths of world population")])
add("test", "text", "How many people in middle-income countries still lacked electricity access according to chapter 3?", "Over 300 million.", [(107,"Climate action discussion","Over 300 million")])
add("test", "text", "By what percentage did the IEA raise its forecast for renewable capacity additions in 2023 and 2024?", "38%.", [(171,"Energy-crisis discussion","Raised by 38 percent")])
add("test", "text", "Approximately what share of its education budget did Korea devote to primary education in the 1950s?", "Nearly 80%.", [(223,"Korea foundational-skills paragraph","Nearly 80 percent")])
add("test", "no_evidence", "What was the observed world population share of low-income economies in 2034?", None, [], "No actual 2034 observation in a 2024 report.")
add("test", "no_evidence", "What was the measured global number of low-carbon job openings in 2029?", None, [], "The report provides 2022 evidence, not observed 2029 job totals.")
add("test", "no_evidence", "Who won the 2028 Nobel Prize in Economics?", None, [], "Event after the 2024 publication.")
add("test", "no_evidence", "What exact 2032 share of global CO2 emissions came from upper-middle-income economies?", None, [], "The table covers 2022, not observed 2032 emissions.")
add("test", "no_evidence", "What was the actual 2035 worldwide share of electricity generated by solar power?", None, [], "No observed 2035 result is available in the report.")
add("test", "no_evidence", "Which country had the most fossil-fuel jobs in 2030?", None, [], "No observed 2030 country ranking appears in the 2024 report.")

assert len(rows) == 48
assert [sum(r["split"] == s and bool(r["gold"]) for r in rows) for s in ("dev", "test")] == [15, 24]
assert [sum(r["split"] == s and not r["gold"] for r in rows) for s in ("dev", "test")] == [3, 6]
assert all(len({(g["page"], g["region"].split(',')[0]) for g in r["gold"]}) >= 2
           for r in rows if r["group"] == "multi_hop")
OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Wrote pilot and replacement {len(rows)}-question benchmark to {OUT}")
