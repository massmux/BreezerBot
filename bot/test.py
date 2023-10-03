import breez_sdk
import os

# https://gist.github.com/dangeross/b1c9a108852aa218b7b8a2e8848aed10

class SDKListener(breez_sdk.EventListener):
   def on_event(self, event):
      print(event)

def mkdir(dir: str):
    try:
        os.mkdir(dir)
    except FileExistsError:
        pass

def get_sdk(self,breez_sdk_api_key: str,
    working_dir: str,
    invite_code: str,
    mnemonic: str,
) -> breez_sdk.BlockingBreezServices:
    # Create working dir
    full_working_dir = os.path.join(os.getcwd(), working_dir)
    mkdir(full_working_dir)
    # Configure and connect
    seed = breez_sdk.mnemonic_to_seed(mnemonic)
    config = breez_sdk.default_config(breez_sdk.EnvironmentType.PRODUCTION, breez_sdk_api_key, breez_sdk.NodeConfig.GREENLIGHT(breez_sdk.GreenlightNodeConfig(None, invite_code)))
    config.working_dir = full_working_dir
    sdk_services = breez_sdk.connect(config, seed, SDKListener())
    self.sdk_services=sdk_services
    # Get node info
    node_info = sdk_services.node_info()
    print(node_info)
    return sdk_services

def multi_sdk_test():
    # Set API key
    breez_sdk_api_key = "8iizkkbD3N1vBLzodFLmcFgyVmy6UCV8B9Cr7cyScZA="
    # Connect
    sdk_1 = get_sdk(breez_sdk_api_key,
                    "/opt/breezerbot/workdir/200260523",
                    "EUZX-QKD9", # Invite code for SDK 1
                    "riot fluid east pet diary toddler pioneer hill nest squirrel zebra stone turn helmet decline black tool couple open tornado pumpkin shove weekend plate", # Mnemonic for SDK 1
    )
    sdk_2 = get_sdk(breez_sdk_api_key,
                    "/opt/breezerbot/workdir/987561327",
                    "KHS9-7QTC", # Invite code for SDK 2
                    "fire recycle clown scrap breeze ignore tomato sunset alarm equip poet fame smoke grain escape depend retire busy pave earth february jazz mask dry", # Mnemonic for SDK 2
    )
    # Disconnect
    sdk_1.disconnect()
    sdk_2.disconnect()

multi_sdk_test()
