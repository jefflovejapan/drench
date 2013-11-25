// TODO -- fix this so it dynamically knows which IP address / port I'm using

(function(){
                window.THEWEBSOCKET = new WebSocket("ws://blagdons-macbook-air-2.local:8001");
                window.THEWEBSOCKET.onopen = function () {console.log("we in here") };
                window.THEWEBSOCKET.onmessage = function (message) {

                    var files = {}



                    var data = JSON.parse(message.data)
                    if (data["kind"] === "init") {
                        build_model(data);
                    } else if (data["kind"] === "request") {
                        vis_request(data);
                    } else if (data["kind"] === "write") {
                        vis_write(data);
                    } else {
                        throw "Data kind invalid"
                    }

                    var build_model = function (init_dict) {
                        for (i in init_dict["want_file_pos"]) {
                            files[i] = {};
                            var head_and_tail = init_dict["heads_and_tails"][i];
                            files[i]["bitfield"] = init_dict["bitfield"]
                                                   [head_and_tail[0]:
                                                    head_and_tail[1] + 1];
                            files[i]["path"] = init_dict["files"][i]["path"];
                            files[i]["relevant"] = [];
                            for (var j = head_and_tail[0]; j <= head_and_tail[1]; j++) {
                                files[i]["relevant"].push(j);
                            }
                        }
                    }

                    var vis_request = function (req_dict) {
                        console.log(req_dict);
                    }

                    var vis_write = function (write_dict) {
                        var index = write_dict["piece_index"];
                        for (var file in files) {
                            var internal_index = file["relevant"].indexOf(index);
                            if ( internal_index !== -1) {
                                file["bitfield"][internal_index] = 0;
                                // TODO -- add transition code here
                                console.log(file["bitfield"]);
                            }
                        }
                    }

                    var h = document.getElementsByTagName('h1')[0];
                    h.innerHTML = data["kind"]};
                document.onclick = function () { window.THEWEBSOCKET.send('o hai there') };
          }())
