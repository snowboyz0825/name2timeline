let filelist;
let totalPlaytime;
let week;
let playerTimeframes;

async function initialize() {
	const response = await fetch("https://name2.party/api/joindb/filelist.json", { cache: "no-cache" });
	if (!response.ok) throw new Error(`Failed to fetch filelist: ${response.status}`);
	filelist = await response.json();
	week = getLatestWeek(filelist);
	await gatherPlaytimeData(week);
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
	totalPlaytime = {};
	playerTimeframes = {};
	for (const player of entries) {
		const playtime = player.exitTime - player.joinTime;
		totalPlaytime[player.playerName] = (totalPlaytime[player.playerName] || 0) + playtime;

		if (!playerTimeframes[player.playerName]) {
			playerTimeframes[player.playerName] = [];
		}
		playerTimeframes[player.playerName].push({
			joinPercent: (player.joinTime % 86400) / 86400,
			leavePercent: (player.exitTime % 86400) / 86400
		});
	}
}

let grid = document.getElementById("timeline-grid");

async function displayShit() {
	await ready;
	for (const name in playerTimeframes) {
		const bar = document.createElement("div");
		bar.className = "day-timeline";
		bar.title = name;
		for (const time of playerTimeframes[name]) {
			const div = document.createElement("div");
			div.className = "session";
			div.style.left = `${time.joinPercent * 100}%`;
			div.style.width = `${(time.leavePercent - time.joinPercent) * 100}%`;
			bar.appendChild(div);
		}
		grid.appendChild(bar);
	}
}

displayShit().catch(console.error);