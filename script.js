async function fetchWeekNumber() {
	let res = await fetch("https://name2.party/api/joindb/filelist.json", { cache: "no-cache" });
	let data = await res.json();
	let week = data[data.length-1];
	let weekNum = week.slice(week.indexOf("W") + 1);
	return(weekNum.slice(0, -6));
}

async function gatherPlaytimeData(week) {
	const currentYear = new Date().getFullYear();
	const response = await fetch(`./data/timelogs/server_${currentYear}-W${week}.jsonl`);
	const dataStringed = await response.text();
	const weekPlaytimeData = dataStringed.split('\n').filter(line => line.trim() !== '').map(line => JSON.parse(line));

	let weekPlaytimeDataOrganized = []
	for (let i = 0; i < weekPlaytimeData; i++) {
		if (weekPlaytimeDataOrganized.includes(weekPlaytimeData[i].playerName)) {
			return
		} else {
			weekPlaytimeDataOrganized.push(playerName);
			console.log(weekPlaytimeDataOrganized)
		}
	}
}