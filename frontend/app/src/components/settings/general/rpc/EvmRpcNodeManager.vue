<script setup lang="ts">
import { type Blockchain } from '@rotki/common/lib/blockchain';
import {
  type EvmRpcNode,
  type EvmRpcNodeList,
  getPlaceholderNode
} from '@/types/settings';

const { t } = useI18n();

const props = defineProps<{
  chain: Blockchain;
}>();

const { chain } = toRefs(props);

const nodes = ref<EvmRpcNodeList>([]);
const editMode = ref(false);
const selectedNode = ref<EvmRpcNode>(getPlaceholderNode(get(chain)));

const { notify } = useNotificationsStore();
const { setMessage } = useMessageStore();

const { setOpenDialog, closeDialog, setPostSubmitFunc } = useEvmRpcNodeForm();

const { connectedNodes } = storeToRefs(usePeriodicStore());
const api = useEvmNodesApi(get(chain));
const { getEvmChainName } = useSupportedChains();

async function loadNodes(): Promise<void> {
  try {
    set(nodes, await api.fetchEvmNodes());
  } catch (e: any) {
    notify({
      title: t('evm_rpc_node_manager.loading_error.title', {
        chain: get(chain)
      }),
      message: e.message
    });
  }
}

onMounted(async () => {
  await loadNodes();
});

const resetForm = () => {
  closeDialog();
  set(selectedNode, getPlaceholderNode(get(chain)));
  set(editMode, false);
};

setPostSubmitFunc(async () => {
  await loadNodes();
  resetForm();
});

const edit = (item: EvmRpcNode) => {
  setOpenDialog(true);
  set(selectedNode, item);
  set(editMode, true);
};

const deleteNode = async (node: EvmRpcNode) => {
  try {
    const identifier = node.identifier;
    await api.deleteEvmNode(identifier);
    await loadNodes();
  } catch (e: any) {
    setMessage({
      title: t('evm_rpc_node_manager.delete_error.title', {
        chain: get(chain)
      }),
      description: e.message,
      success: false
    });
  }
};

const onActiveChange = async (active: boolean, node: EvmRpcNode) => {
  const state = { ...node, active };
  try {
    await api.editEvmNode(state);
    await loadNodes();
  } catch (e: any) {
    setMessage({
      title: t('evm_rpc_node_manager.activate_error.title', {
        node: node.name
      }),
      description: e.message,
      success: false
    });
  }
};

const isEtherscan = (item: EvmRpcNode) =>
  !item.endpoint && item.name.includes('etherscan');

const isNodeConnected = (item: EvmRpcNode): boolean => {
  const blockchain = get(chain);
  const connected = get(connectedNodes);
  const evmChain = getEvmChainName(blockchain);
  const nodes = evmChain && connected[evmChain] ? connected[evmChain] : [];

  return nodes.includes(item.name) || isEtherscan(item);
};

const { show } = useConfirmStore();

const showDeleteConfirmation = (item: EvmRpcNode) => {
  const chainProp = get(chain);
  show(
    {
      title: t('evm_rpc_node_manager.confirm.title', { chain: chainProp }),
      message: t('evm_rpc_node_manager.confirm.message', {
        node: item.name,
        endpoint: item.endpoint,
        chain: chainProp
      })
    },
    () => deleteNode(item)
  );
};

const css = useCssModule();
</script>

<template>
  <div>
    <v-card outlined>
      <v-list max-height="300px" :class="css.list" three-line class="py-0">
        <template v-for="(item, index) in nodes">
          <v-divider v-if="index !== 0" :key="index" />
          <v-list-item
            :key="index + item.name"
            data-cy="ethereum-node"
            class="px-2"
          >
            <div class="mr-2 pa-4 text-center d-flex flex-column align-center">
              <div>
                <v-tooltip v-if="!item.owned" top open-delay="400">
                  <template #activator="{ on, attrs }">
                    <v-icon v-bind="attrs" v-on="on"> mdi-earth </v-icon>
                  </template>
                  <span>{{ t('evm_rpc_node_manager.public_node') }}</span>
                </v-tooltip>
                <v-tooltip v-else>
                  <template #activator="{ on, attrs }">
                    <v-icon v-bind="attrs" v-on="on">
                      mdi-account-network
                    </v-icon>
                  </template>
                  <span>{{ t('evm_rpc_node_manager.private_node') }}</span>
                </v-tooltip>
              </div>

              <div class="mt-2">
                <v-tooltip v-if="isNodeConnected(item)" top open-delay="400">
                  <template #activator="{ on, attrs }">
                    <v-icon v-bind="attrs" small color="green" v-on="on">
                      mdi-wifi
                    </v-icon>
                  </template>
                  <span>
                    {{ t('evm_rpc_node_manager.connected.true') }}
                  </span>
                </v-tooltip>
                <v-tooltip v-else top open-delay="400">
                  <template #activator="{ on, attrs }">
                    <v-icon v-bind="attrs" small color="red" v-on="on">
                      mdi-wifi-off
                    </v-icon>
                  </template>
                  <span>
                    {{ t('evm_rpc_node_manager.connected.false') }}
                  </span>
                </v-tooltip>
              </div>
            </div>

            <v-list-item-content>
              <v-list-item-title class="font-weight-medium">
                {{ item.name }}
              </v-list-item-title>
              <v-list-item-subtitle>
                <div v-if="!isEtherscan(item)">
                  {{ item.endpoint }}
                </div>
                <div v-else>
                  {{ t('evm_rpc_node_manager.etherscan') }}
                </div>
                <div class="mt-1" :class="css.weight">
                  <span v-if="!item.owned">
                    {{
                      t('evm_rpc_node_manager.weight', {
                        weight: item.weight
                      })
                    }}
                  </span>
                  <span v-else>
                    {{ t('evm_rpc_node_manager.private_node_hint') }}
                  </span>
                </div>
              </v-list-item-subtitle>
            </v-list-item-content>
            <v-switch
              value=""
              :input-value="item.active"
              :disabled="isEtherscan(item)"
              @change="onActiveChange($event, item)"
            />
            <v-list-item-action :class="css.centered">
              <v-row align="center" justify="center">
                <v-col>
                  <row-actions
                    :delete-tooltip="t('evm_rpc_node_manager.delete_tooltip')"
                    :delete-disabled="isEtherscan(item)"
                    :edit-tooltip="t('evm_rpc_node_manager.edit_tooltip')"
                    @edit-click="edit(item)"
                    @delete-click="showDeleteConfirmation(item)"
                  />
                </v-col>
              </v-row>
            </v-list-item-action>
          </v-list-item>
        </template>
      </v-list>

      <evm-rpc-node-form-dialog
        v-model="selectedNode"
        :chain="chain"
        :edit-mode="editMode"
        :is-etherscan="editMode && isEtherscan(selectedNode)"
        @reset="resetForm()"
      />
    </v-card>

    <div class="pt-8">
      <v-btn
        depressed
        color="primary"
        data-cy="add-node"
        @click="setOpenDialog(true)"
      >
        {{ t('evm_rpc_node_manager.add_button') }}
      </v-btn>
    </div>
  </div>
</template>

<style module lang="scss">
.list {
  overflow-y: auto;
  overflow-x: hidden;
}

.weight {
  font-size: 13px;
}

.centered {
  align-self: center !important;
}
</style>
