/* timelineGrid = document.getElementById('timeline-grid')


const timelineData = require('./data/timelogs/'); 
function renderGrid() {
    
}


const today = new Date();
const year = today.getFullYear();
const startOfYear = new Date(year, 0, 1);
const pastDaysOfYear = (today - startOfYear) / 86400000;
const week = Math.ceil((pastDaysOfYear + startOfYear.getDay() + 1) / 7);

console.log("Year:", year);
console.log("Week:", week);


 */

/* Testing specific dates where the two week-numbering systems disagree.
No, it won’t match. It’s the common “week of year” formula, but it counts weeks a different way than Python’s isocalendar():

Your formula	ISO (what Python uses)
Week starts	Sunday (getDay())	Monday
Week 1 is	the week containing Jan 1	the week containing the first Thursday
Year	calendar year	ISO year (can differ near New Year)
It gives the right number on many dates, which makes the mismatch easy to miss. The cases where it fails:

Date	Your formula	Python
Sun 2026-10-18	2026-W43	2026-W42
Fri 2027-01-01	2027-W01	2026-W53
Sun 2023-01-01	2023-W01	2022-W52
Every Sunday would land in the next week’s file. At New Year you’d request a file that doesn’t exist, or the wrong one. It also depends on local time unless startOfYear and the day count are both built with UTC.

Use the Thursday-shift version, which handles all three points: */

/* function weekFileName(date = new Date()) {
  const d = new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate()));
  d.setUTCDate(d.getUTCDate() + 4 - (d.getUTCDay() || 7)); // Thursday of this ISO week
  const isoYear = d.getUTCFullYear();
  const isoWeek = Math.ceil(((d - Date.UTC(isoYear, 0, 1)) / 864e5 + 1) / 7);
  return `server_${isoYear}-W${String(isoWeek).padStart(2, "0")}.jsonl`;
}

*/

async function test() {
	const res = await fetch("https://name2.party/api/joindb/filelist.json", { cache: "no-cache" });
	console.log(res)
	const data = await res.json();
	console.log(data)
	let week = data[data.length-1];
	week = "2026_W1234.jsonl"
	console.log(week)
	let weekNum = week.slice(week.indexOf("W") + 1);
	console.log(weekNum.slice(0, -6));
}