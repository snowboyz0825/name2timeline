let res

async function fetchIntialData() {
	res = await fetch("https://name2.party/api/joindb/filelist.json", { cache: "no-cache" });
}

ready = fetchIntialData();

async function initialize() {
	await ready;
	// const weekNum = await fetchWeekNumber();
	const weekPlaytimeDataOrganized = await gatherPlaytimeData("32");
	console.log(weekPlaytimeDataOrganized);
}

async function fetchWeekNumber() {
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

	let playerTimesOrganized = {}
	for (let i = 0; i < weekPlaytimeData.length; i++) {
		let name = weekPlaytimeData[i].playerName
		let playtimeToAdd = weekPlaytimeData[i].exitTime - weekPlaytimeData[i].joinTime;
		playerTimesOrganized[name] = (playerTimesOrganized[name] || 0) + playtimeToAdd;
	}


	/* for (let i = 0; i < weekPlaytimeData.length; i++) {
			let name = weekPlaytimeData[i].playerName
			let playtimeToAdd = weekPlaytimeData[i].exitTime - weekPlaytimeData[i].joinTime;
		if (!weekPlaytimeDataOrganized[i].username == name) {
			weekPlaytimeDataOrganized.push({
				username: name,
				playtimeSeconds: playtimeToAdd
			});
		} else
			{
				weekPlaytimeDataOrganized[i].playtimeSeconds += playtimeToAdd
		}
	}
	return(weekPlaytimeDataOrganized); */
}