let filelist;
let totalPlaytime;
let week;

async function initialize() {
	const response = await fetch("https://name2.party/api/joindb/filelist.json", { cache: "no-cache" });
	if (!response.ok) throw new Error(`Failed to fetch filelist: ${response.status}`);
	filelist = await response.json();
	week = getLatestWeek(filelist);
	totalPlaytime = await gatherPlaytimeData(week);
}

const ready = initialize();

function getLatestWeek(files) {
	if (files.length === 0) throw new Error("Filelist is empty");
	const file = files[files.length - 1];
	return file.slice(file.indexOf("_") + 1, -6);
}

async function gatherPlaytimeData(week) {
	const response = await fetch(`./data/timelogs/server_${week}.jsonl`);
	if (!response.ok) throw new Error(`Failed to fetch timelog for ${week}: ${response.status}`);
	const text = await response.text();
	const entries = text.split("\n").filter(line => line.trim() !== "").map(line => JSON.parse(line));
	const playerTimes = {};
	const playerTimeframes = {};
	for (const player of entries) {
		const playtime = player.exitTime - player.joinTime;
		playerTimes[player.playerName] = (playerTimes[player.playerName] || 0) + playtime;

		const timeframeJoinPercent = player.jointime/86400;
		const timeframeLeavePercent = player.exitTime/86400;
		
	}
	return playerTimes;
}