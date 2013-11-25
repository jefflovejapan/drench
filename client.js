// TODO -- fix this so it dynamically knows which IP address / port I'm using

(function(){
                window.THEWEBSOCKET = new WebSocket("ws://blagdons-macbook-air-2.local:8001");
                window.THEWEBSOCKET.onopen = function () {console.log("we in here") };

                var files = {};
                var want_file_pos = [];

                var build_model = function (init_dict) {
                    want_file_pos = init_dict["want_file_pos"]
                    want_file_pos.forEach( function(file_pos) {
                        files[file_pos] = {};
                        var head_and_tail = init_dict["heads_and_tails"][file_pos];
                        files[file_pos]["bitfield"] = '';
                        for (var j = head_and_tail[0]; j <= head_and_tail[1]; j++) {
                            files[file_pos]["bitfield"] = files[file_pos]["bitfield"] +
                                                   init_dict["bitfield"][j];
                        }
                        files[file_pos]["path"] = init_dict["files"][file_pos]["path"];
                        files[file_pos]["relevant"] = [];
                        for (var j = head_and_tail[0]; j <= head_and_tail[1]; j++) {
                            files[file_pos]["relevant"].push(j);
                        }
                    });
                }

                var vis_request = function (req_dict) {
                    console.log(req_dict);
                }

                var vis_write = function (write_dict) {
                    console.log(write_dict);
                    var piece_index = write_dict["piece"];
                    // Want to find which files care about piece_index
                    files.forEach( function (afile) {
                        var internal_index = afile["relevant"].indexOf(piece_index);
                        console.log(internal_index);
                        if ( internal_index !== -1) {
                            afile["bitfield"][internal_index] = 0;
                            // TODO -- add transition code here
                            console.log(afile["bitfield"]);
                        }
                    }
                }

                window.THEWEBSOCKET.onmessage = function (message) {
                    var meat = JSON.parse(message.data);
                    if (meat["kind"] === "init") {
                        build_model(meat);
                    } else if (meat["kind"] === "request") {
                        vis_request(meat);
                    } else if (meat["kind"] === "write") {
                        vis_write(meat);
                    } else {
                        throw "Data kind invalid"
                    }
                    var h = document.getElementsByTagName('h1')[0];
                    h.innerHTML = meat["kind"];
                }

                document.onclick = function () { window.THEWEBSOCKET.send('o hai there') };
}) ();
