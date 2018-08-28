# Copyright 2018 Admiralty Technologies Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import yaml


class Controller(BaseHTTPRequestHandler):
    def sync(self, parent, children):
        legacy_mapping = {
            "apiVersion": "ambassador/v0",
            "kind": "Mapping",
            "name":  parent["metadata"]["name"],
        }
        spec = parent.get("spec", {})
        spec.pop("selector", None)
        legacy_mapping.update(spec)

        a = yaml.dump(legacy_mapping, explicit_start=True)

        ds_name = parent["metadata"]["name"] + "-ambassadorshim"
        ds = {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": ds_name,
                "annotations": {
                    "getambassador.io/config": a,
                },
            },
            "spec": {
                "ports": [{
                    "port": 80,
                }],
            },
        }

        configured = ds_name in children["Service.v1"]
        up_to_date = configured and children["Service.v1"][ds_name] \
            .get("metadata", {}) \
            .get("annotations", {}) \
            .get("getambassador.io/config", "") == a
        status = {
            "configured": configured,
            "upToDate": up_to_date,
        }

        return {"status": status, "children": [ds]}

    def do_POST(self):
        observed = json.loads(self.rfile.read(
            int(self.headers.get("content-length"))))
        desired = self.sync(observed["parent"], observed["children"])

        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(desired).encode())


HTTPServer(("", 80), Controller).serve_forever()
