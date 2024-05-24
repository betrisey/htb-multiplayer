from flask import Flask, request, jsonify, render_template, flash, redirect, send_file
from sshpubkeys import SSHKey
import os
import sys
import subprocess
import tempfile
import re

HTB_SUBNET = os.getenv("HTB_SUBNET")
FORWARDING = {}

app = Flask(__name__)
app.secret_key = os.urandom(16)

@app.get("/")
def index():
    return render_template("index.html", HTB_SUBNET=HTB_SUBNET, FORWARDING=FORWARDING)

@app.post("/create-user")
def create():
    username = request.form["username"]
    if not re.match(r"^[a-zA-Z0-9]+$", username):
        flash("Invalid username", "error")
        return redirect("/")
    try:
        ssh_key = request.files["ssh_key"].read().decode("utf-8")
    except Exception as e:
        flash("invalid SSH public key: " + str(e), "error")
        return redirect("/")

    ssh = SSHKey(ssh_key, strict=True)
    try:
        ssh.parse()
        with open("/root/.ssh/authorized_keys", "a") as f:
            f.writelines([ssh_key])
    except Exception as e:
        flash("invalid SSH public key: " + str(e), "error")
    
    operator_cfg_file = tempfile.mktemp()
    #os.system(f"/opt/sliver-server operator --lhost {request.host} --name {username} -s {operator_cfg_file}")
    # prevent command injection
    subprocess.run(["/opt/sliver-server", "operator", "--lhost", request.host, "--name", username, "-s", operator_cfg_file], check=True)

    flash("SSH key added, operator created", "success")
    
    return send_file(operator_cfg_file, as_attachment=True, download_name=f"{username}.cfg")

@app.post("/port-forward")
def port_forward():
    destination_ip = request.remote_addr
    destination_port = int(request.form["destination_port"])
    listening_port = int(request.form["source_port"])

    port_used = len(subprocess.run(f"ss -tln | grep :{listening_port}", shell=True, stdout=subprocess.PIPE).stdout) > 0
    if port_used:
        flash(f"Port {listening_port} is already in use", "error")
    
    if not port_used:
        FORWARDING[listening_port] = {
            "destination_ip": destination_ip,
            "destination_port": destination_port,
            "listening_port": listening_port
        }

        # start socat in background
        os.system(f"nohup socat tcp-listen:{listening_port},fork,reuseaddr tcp:{destination_ip}:{destination_port} &")

        flash(f"Port {listening_port} forwarded to {destination_ip}:{destination_port}", "success")

    return redirect("/")

@app.post("/stop-port-forward")
def stop_port_forward():
    listening_port = int(request.form["listening_port"])
    if listening_port not in FORWARDING:
        flash(f"Port {listening_port} is not being forwarded", "error")
        return redirect("/")
    
    os.system(f"kill $(lsof -t -i:{listening_port})")

    FORWARDING.pop(listening_port, None)
    flash(f"Forwarding to port {listening_port} removed", "success")
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
