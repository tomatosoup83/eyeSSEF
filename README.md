# stolen by patrick, modified pipeline

Finally friggin work, time to sleep

## have u ever went to sawcon

---

## How to run:
make a plr_inbox folder on user on mac then just go to the eyessef_modified, in my case it's:

```bash
conda activate eyessef

cd "/Users/ptrckhanzel/Documents/SSEF Related/eyeSSEF_modified"

python watch_inbox.py \
  --inbox "/Users/ptrckhanzel/plr_inbox" \
  --repo "/Users/ptrckhanzel/Documents/SSEF Related/eyeSSEF_modified"

  ```

whenever there's a video let's say from the Pi to the plr_inbox it will automatically process the thing

Now how to install things on the pi
1st things 1st

```bash
sudo apt update
sudo apt install -y rsync inotify-tools openssh-client

ssh-keygen -t ed25519 -C "pi-plr-autosend"
# press Enter through defaults (so no password lah)
cat ~/.ssh/id_ed25519.pub

then u get key do things on mac

after that create new sh

nano ~/plr_autosend.sh

refer to autosend.sh thing here

chmod +x ~/plr_autosend.sh

~/plr_autosend.sh
```

yay
