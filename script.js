async function fetchWeekNumber() {
	let res = await fetch("https://name2.party/api/joindb/filelist.json", { cache: "no-cache" });
	let data = await res.json();
	let week = data[data.length-1];
	let weekNum = week.slice(week.indexOf("W") + 1);
	return(weekNum.slice(0, -6));
}