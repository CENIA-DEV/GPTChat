# Cenia Chat

## Install

### Method 1: With pip

```bash
pip3 install "fschat[model_worker,webui]"
```

## Run Cenia chat
the following scripts are intended to run cenia-chat using ranokau, a gcp instance and a bucket
TODO create and activate an env
in ranokau run the next bash file
```bash
chmod +x /cenia-scripts/run_models.sh
./cenia-scripts/run_models.sh
```

then in the gcp instance run to open ssh tunnels between ranokau and the instance
```bash
chmod +x /cenia-scripts/open_tunnels.sh
./cenia-scripts/open_tunnels.sh
```

and finally run the webui bash. this bash run a simple server to save the converstaions logs in a bucket and then run the webui
```bash
chmod +x /cenia-scripts/run_webui.sh
./cenia-scripts/run_webui.sh
```
