var http = require('http');
var handlebars = require('handlebars');
var fs = require('fs');
var static = require('node-static');

var co = require('co');
var sqlite3 = require("co-sqlite3");

const PORT=80; 
var template;

var COST_OF_SERVER = 20; //dollars

var file = new static.Server('./static');


function handleRequest(request, response){

    if(request.url=='/index.html' || request.url=='/') {
        fs.readFile('index.html', 'utf-8', function(error, source){
            global.template = handlebars.compile(source);
            var data = {};
            response.end(global.template(data));
        });
    }else if(request.url=='/status.html') {
        fs.readFile('status.html', 'utf-8', function(error, source){
	    if(error){
		console.error(error);
	    }
            var status_tmp = handlebars.compile(source);
			co(getPlaytimeData()).then(function(data){
				response.end(status_tmp({"data":data}));
			}).catch(function(err){console.error("ERROR" + err);});
        });
    }else if(request.url=='/fibs.html') {
        fs.readFile('fibs.html', 'utf-8', function(error, source){
            global.template = handlebars.compile(source);
            var data = {};
            response.end(global.template(data));
        });
    }else{
       request.addListener('end', function(){
           file.serve(request,response);
       }).resume();
    }
}

var server = http.createServer(handleRequest);

//Lets start our server
server.listen(PORT, function(){
    console.log("Server listening on: http://localhost:%s", PORT);
});
console.log("DONE");

//database connection


var db_file = "/var/minecraft/mc.db"
var db;

sqlite3(db_file).then(function(database){
	db = database;
});;
/*

var getTables = function*(){
	console.log("get tables");
	var tables = {players:[]};
	var queue = [];
	yield db.each("SELECT * from players;", [], co(function*(err,row){
		playtime = getPlaytime(
			row.uuid, 
			new Date(0), 
			new Date()
		).then(function(pt){row.playtime = pt;}));
		tables.players.push(row);
		console.log("got row");
	}));
	
	.then(function(){
		console.log("got tabless");
		console.log(queue);
		Promise.all(queue, function(){console.log("resolving tables");resolve(tables);});
	});
}
*/

var getPlaytime = function*(uuid, from_dt, to_dt){
	var playtime = 0;
	// Get session 1 time if from_dt exists
	/*var rows = yield db.all(
			"SELECT SUM(( JulianDay(end) - JulianDay(?) ) * 24 ) " +
			"from sessions where uuid = ?", [formatDatetime(from_dt), uuid]);
	console.log(rows);
	if(rows.length > 0){
		playtime += rows[0][0];
	}
	*/
	
	// session 2
	rows = yield db.all(
			"SELECT SUM(( JulianDay(end) - JulianDay(start) ) * 24 ) " +
				"from sessions where uuid = ? and start > ? and end < ?", [
				uuid, 
				formatDatetime(from_dt), 
				formatDatetime(to_dt)
	]);
	if(rows.length > 0){
		for(query in rows[0]){
			if(rows[0][query] !== null && rows[0][query] !== undefined)
				playtime += rows[0][query];
		}
	}
	/*
	console.log("PT: " + uuid + " q3");
	rows = yield db.all(// Get session 3 if to_dt exists
			"SELECT SUM(( JulianDay(?) - JulianDay(start) ) * 24 ) " +
			"from sessions where uuid = ?", [formatDatetime(to_dt), uuid]);
	console.log(rows);
	if(rows.length > 0){
		playtime += ro*ws[0][0];
	}*/
	return playtime;
};

var months = ["January", "February", "March", "April", "May", "June", "July","August", "September", "November", "December"];

var getPlaytimeForMonthAgo = function*(monthsAgo){
	var players = yield db.all("SELECT * from players;");
	var today = new Date();
	var start_of_month = new Date(today.getFullYear(), today.getMonth() - monthsAgo);
	var end_of_month = new Date(today.getFullYear(), today.getMonth() - monthsAgo+1);
	
	var total_playtime = 0;
	
	var result = {
		"month": months[start_of_month.getMonth()],
		"players": [],
	};
	for(var p in players){
		if(p !== undefined){
			var playtime = yield co(getPlaytime(
				players[p].uuid, 
				start_of_month, 
				end_of_month
			)).catch(function(err){console.log("GOT error");console.error(err);});
			if(playtime > 0){
				result["players"].push({
					"username": players[p].username,
					"playtime": Math.round(playtime*100)/100
				});
				total_playtime += playtime;
			}
		}
	}
	//sort biggest playtime first
	result["players"].sort(function(x, y){return y["playtime"] - x["playtime"];});
	for(var p in result["players"]){
		if(p !== undefined){
			result["players"][p].percent = Math.round(
				result["players"][p].playtime/total_playtime
			*100*100)/100;
			if(monthsAgo > 0){
				result["players"][p]["donation"] = (
					Math.round(COST_OF_SERVER * result["players"][p].percent/100));
			}
		}
	}
	result["total_playtime"] =  Math.round(total_playtime*100)/100
	//console.log("Getting Playtime from " + formatDatetime(start_of_month) + " to " + formatDatetime(end_of_month));
	console.log(result);
	return result;
};

var getPlaytimeData = function*(){

	var data = [];
	for(var i=0;i<4;i++){
		//console.log("GETTING PT DATA FOR " +  i);
		data[i] = yield co(getPlaytimeForMonthAgo(i)).catch(function(err){console.log("GOTten error");console.error(err);});
	}
	return data;
}


var formatDatetime = function(d){
	return d.getFullYear()+"-"+
	pad((d.getMonth()+1),2)+ "-" +
	pad(d.getDate(),2) + " " +
	pad(d.getHours(),2) + ":" +
	pad(d.getMinutes(),2) + ":" +
	pad(d.getSeconds(),2);
};

//http://stackoverflow.com/a/10073788
function pad(n, width, z) {
  z = z || '0';
  n = n + '';
  return n.length >= width ? n : new Array(width - n.length + 1).join(z) + n;
}

//db.close();
