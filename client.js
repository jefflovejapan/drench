// TODO -- fix this so it dynamically knows which IP address / port I'm using

(function(){
                window.THEWEBSOCKET = new WebSocket("ws://blagdons-macbook-air-2.local:8001");
                window.onbeforeunload = function () { window.THEWEBSOCKET.close(); };

                var files = {};
                var want_file_pos = [];

                var build_model = function (init_dict) {
                    want_file_pos = init_dict["want_file_pos"]
                    want_file_pos.forEach( function(file_pos, i) {
                        files[file_pos] = {};
                        var head_and_tail = init_dict["heads_and_tails"][i];
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
                    var piece_index = write_dict["piece_index"];
                    // Want to find which files care about piece_index
                    for (file_index in files) {
                        var internal_index = files[file_index]["relevant"].indexOf(piece_index);
                        console.log(internal_index);
                        if ( internal_index !== -1) {
                            // TODO -- add transition code here
                            console.log(files[file_index]["path"] + ' cares about ' + piece_index);
                        }
                    };
                }

                window.THEWEBSOCKET.onmessage = function (message) {
                    var meat = JSON.parse(message.data);
                    console.log(meat["kind"]);
                    if (meat["kind"] === "init") {
                        build_model(meat);
                    } else if (meat["kind"] === "request") {
                        vis_request(meat);
                    } else if (meat["kind"] === "piece") {
                        vis_write(meat);
                    } else {
                        throw "Data kind invalid";
                    }
                    var h = document.getElementsByTagName('h1')[0];
                    h.innerHTML = meat["kind"];
                }

                document.onclick = function () { window.THEWEBSOCKET.send('o hai there') };
}) ();
