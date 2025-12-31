import requests
import tkinter as tk
from tkinter import messagebox
import datetime
from tkinter import ttk

root = tk.Tk()
root.title("Linode Controller")
root.geometry("400x300")

try:
    with open("api.txt", "r") as f:
        for line in f:
            API_TOKEN = line    
except FileNotFoundError:
    print("api.txt does not exist!")

try:
    HEADERS = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json",
    }
except NameError:
    print("api.txt may not exist")

# Map Linode IDs to names
# idAndNames = {89221831: "TSNode1"}
idAndNames = {}

colors = {
        "running": "green",
        "offline": "red",
        "provisioning": "blue",
        "unknown": "gray",
        "shutting_down": "orange",
        "booting": "orange"
}

def get_linodes():
    url = "https://api.linode.com/v4/linode/instances"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()

    idAndNames.clear()

    for linode in response.json()["data"]:
        linode_id = linode["id"]
        label = linode["label"]
        idAndNames[linode_id] = label

def get_ip():
    url = f"https://api.linode.com/v4/linode/instances/{selected_linode_id}"
    r = requests.get(url, headers=HEADERS)

    # print(r.status_code)
    # print(r.json())
    data = r.json()
    linode_ipv4 = ", ".join(data["ipv4"])
    linode_ipv6 = data["ipv6"]
    ipv4Label.set(linode_ipv4)
    ipv6Label.set(linode_ipv6)

get_linodes()

display_options = {
    f"{linode_id} - {name}": linode_id
    for linode_id, name in idAndNames.items()
}

def selection_changed(display_text):
    global selected_linode_id
    selected_linode_id = display_options[display_text]
    print(f"Selected Linode ID: {selected_linode_id}")

def power_on():
    if messagebox.askyesno("Are you sure?", "Are you sure you want to power on the Linode?") == True:
        powerOnBtn.config(state=tk.DISABLED)
        url = f"https://api.linode.com/v4/linode/instances/{selected_linode_id}/boot"
        response = requests.post(url, headers=HEADERS)
        if response.ok:
            infoLabelVar.set("Linode is powering on")
            root.after(5000, infoLabelVar.set("..."))
            get_status_no_ip()
        else:
            messagebox.showerror("Error", response.text)

def power_off():
    if messagebox.askyesno("Are you sure?", "Are you sure you want to power off the Linode?") == True:
        powerOffBtn.config(state=tk.DISABLED)
        powerOnBtn.config(state=tk.ACTIVE)
        url = f"https://api.linode.com/v4/linode/instances/{selected_linode_id}/shutdown"
        response = requests.post(url, headers=HEADERS)
        if response.ok:
            infoLabelVar.set("Linode is shutting down")
            root.after(5000, infoLabelVar.set("..."))
            get_status_no_ip()
        else:
            messagebox.showerror("Error", response.text)

def get_status():
    getStatusBtn.config(state=tk.DISABLED)
    infoLabelVar.set("Getting status...")
    root.update_idletasks()
    url = f"https://api.linode.com/v4/linode/instances/{selected_linode_id}"
    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()
    status = r.json()["status"]
    statusLabel.config(fg=colors.get(status, "black"))
    statusLabelVar.set(f"{selected_linode_id}: {status}")
    infoLabelVar.set("Getting Linode IP...")
    root.update_idletasks()
    get_ip()
    infoLabelVar.set("Getting usage quota...")
    root.update_idletasks()
    get_quota()
    last_updated()
    if auto_refresh_var.get():
        root.after(60000, get_status)
    infoLabelVar.set("...")
    getStatusBtn.config(state=tk.ACTIVE)
    return status

def get_status_no_ip():
    getStatusBtn.config(state=tk.DISABLED)
    infoLabelVar.set("Getting status...")
    root.update_idletasks()
    url = f"https://api.linode.com/v4/linode/instances/{selected_linode_id}"
    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()
    status = r.json()["status"]
    statusLabel.config(fg=colors.get(status, "black"))
    statusLabelVar.set(f"{selected_linode_id}: {status}")
    infoLabelVar.set("...")

def copy_ipv4():
    root.clipboard_append(ipv4Label.get())
    infoLabelVar.set("IPv4 address copied to clipboard")
    root.after(5000, lambda: infoLabelVar.set("..."))

def copy_ipv6():
    root.clipboard_append(ipv6Label.get())
    infoLabelVar.set("IPv6 address copied to clipboard")
    root.after(5000, lambda: infoLabelVar.set("..."))

def last_updated():
    lastUpdatedTime = datetime.datetime.now().replace(microsecond=0)  # strip microseconds
    lastUpdatedLabel.set(f"Last updated: {lastUpdatedTime.strftime("%Y-%m-%d %H:%M:%S")}")

def get_quota():
    url = "https://api.linode.com/v4/account/transfer"
    getStatusBtn.config(state=tk.DISABLED)
    infoLabelVar.set("Getting usage quota...")
    root.update_idletasks()
    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()
    usedOfQuota = r.json()["used"]
    entireQuota = r.json()["quota"]
    getQuotaVar.set(f"Network transfer: {usedOfQuota} GB used of {entireQuota} GB ({usedOfQuota / entireQuota * 100:.1f}%)")
    ratio = usedOfQuota / entireQuota

    if ratio >= 0.85:
        getQuotaLabel.config(fg="red")
    elif ratio >= 0.75:
        getQuotaLabel.config(fg="orange")
    elif ratio >= 0.65:
        getQuotaLabel.config(fg="yellow")
    infoLabelVar.set("...")
    getStatusBtn.config(state=tk.ACTIVE)

# Currently selected Linode ID
selected_linode_id = next(iter(idAndNames))

# url = f"https://api.linode.com/v4/linode/instances/{selected_linode_id}"
# r = requests.get(url, headers=HEADERS)
# print(r.status_code)
# print(r.json())

# Dropdown
selected_display = tk.StringVar()
selected_display.set(next(iter(display_options)))

idMenu = tk.OptionMenu(
    root,
    selected_display,
    *display_options.keys(),
    command=selection_changed
)
idMenu.pack(pady=5)

statusLabelVar = tk.StringVar(value="unknown")
statusLabel = tk.Label(root, textvariable=statusLabelVar)
statusLabel.pack(padx=5)

copy_button_frame = tk.Frame(root)
copy_button_frame.pack(pady=5)

tk.Button(copy_button_frame, text="Copy IPv4", command=copy_ipv4).pack(side="left", padx=5)
tk.Button(copy_button_frame, text="Copy IPv6", command=copy_ipv6).pack(side="left", padx=5)

lastUpdatedLabel = tk.StringVar(value="unknown")
tk.Label(root, textvariable=lastUpdatedLabel).pack()

ipv4Label = tk.StringVar(value="unknown")
ipv6Label = tk.StringVar(value="unknown")

tk.Label(root, textvariable=ipv4Label).pack()
tk.Label(root, textvariable=ipv6Label).pack()

power_button_frame = tk.Frame(root)
power_button_frame.pack(pady=5)

powerOnBtn = tk.Button(power_button_frame, text="Power On", command=power_on)
powerOffBtn = tk.Button(power_button_frame, text="Power Off", command=power_off)
powerOnBtn.pack(side="left", padx=5)
powerOffBtn.pack(side="left", padx=5)

usageQuotaFrame = tk.Frame(root)
usageQuotaFrame.pack(pady=5)
getQuotaBtn = tk.Button(usageQuotaFrame, text="Get usage quota", command=get_quota)
getQuotaBtn.pack(padx=5, side="left")
getQuotaVar = tk.StringVar(value="unknown")
getQuotaLabel = tk.Label(usageQuotaFrame, textvariable=getQuotaVar)
getQuotaLabel.pack(padx=5, side="left")

statusCntrlsFrame = tk.Frame(root)
statusCntrlsFrame.pack(pady=5)

auto_refresh_var = tk.BooleanVar(value=True)

auto_refresh_cb = tk.Checkbutton(
    statusCntrlsFrame,
    text="Auto refresh every 60s",
    variable=auto_refresh_var
)
auto_refresh_cb.pack(side="left", padx=5)

getStatusBtn = tk.Button(
    statusCntrlsFrame,
    text="Check Status",
    command=get_status,
    width=18
)
getStatusBtn.pack(side="left", padx=5)

infoLabelFrame = tk.Frame(root)
infoLabelFrame.pack(fill="x", pady=5)
separator = ttk.Separator(infoLabelFrame, orient="horizontal")
separator.pack(fill="x", pady=(0, 4))
infoLabelVar = tk.StringVar(value="...")
infoLabel = tk.Label(infoLabelFrame, textvariable=infoLabelVar)
infoLabel.pack(side="bottom")

if __name__ == "__main__":
    get_linodes()
    if "running" in get_status():
        powerOnBtn.config(state=tk.DISABLED)
    elif "offline" in get_status():
        powerOffBtn.config(state=tk.DISABLED)
    root.mainloop()
