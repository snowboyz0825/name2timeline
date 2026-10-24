let filelist
let totalPlaytime
let week
let ready

async function fetchIntialData() {
	filelist = await fetch("https://name2.party/api/joindb/filelist.json", { cache: "no-cache" });
}

ready = fetchIntialData();
initialize();

async function initialize() {
	await ready;
	week = await fetchWeekNumber();
	totalPlaytime = await gatherPlaytimeData(week);
	const weekPlaytimeDataOrganized = await gatherPlaytimeData(week);
}

async function fetchWeekNumber() {
	let data = await filelist.json();
	let week = data[data.length-1];
	let weekNum = week.slice(week.indexOf("W") + 1);
	return(weekNum.slice(0, -6));
}

async function gatherPlaytimeData(week) {
	const currentYear = new Date().getFullYear();
	const response = await fetch(`./data/timelogs/server_${currentYear}-W${week}.jsonl`);
	const dataStringed = await response.text();
	const weekPlaytimeData = dataStringed.split('\n').filter(line => line.trim() !== '').map(line => JSON.parse(line));

	let playerTimesOrganized = {}
	for (let i = 0; i < weekPlaytimeData.length; i++) {
		let name = weekPlaytimeData[i].playerName
		let playtimeToAdd = weekPlaytimeData[i].exitTime - weekPlaytimeData[i].joinTime;
		playerTimesOrganized[name] = (playerTimesOrganized[name] || 0) + playtimeToAdd;
	}

	return(playerTimesOrganized)
}