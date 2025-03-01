<template>
    <div
        :id="contentId"
        :class="['content-item m-1 p-0 rounded', contentCls]"
        draggable
        :data-hid="id"
        :data-state="state"
        @dragstart="onDragStart">
        <div class="p-1 cursor-pointer" @click.stop="onClick">
            <div class="d-flex justify-content-between">
                <span class="p-1 font-weight-bold">
                    <span v-if="selectable" class="selector">
                        <icon
                            v-if="selected"
                            fixed-width
                            size="lg"
                            :icon="['far', 'check-square']"
                            @click.stop="$emit('update:selected', false)" />
                        <icon
                            v-else
                            fixed-width
                            size="lg"
                            :icon="['far', 'square']"
                            @click.stop="$emit('update:selected', true)" />
                    </span>
                    <span v-if="hasStateIcon">
                        <icon fixed-width :icon="contentState.icon" :spin="contentState.spin" />
                    </span>
                    <span class="id hid">{{ id }}</span>
                    <span>:</span>
                    <span class="content-title name">{{ name }}</span>
                    <CollectionDescription v-if="!isDataset" :item="item" />
                    <div v-if="item.tags && item.tags.length > 0" class="nametags">
                        <Nametag v-for="tag in item.tags" :key="tag" :tag="tag" />
                    </div>
                </span>
                <span class="align-self-start btn-group">
                    <b-button
                        v-if="isDataset"
                        :disabled="displayDisabled"
                        :title="displayButtonTitle"
                        class="px-1"
                        size="sm"
                        variant="link"
                        @click.stop="onDisplay">
                        <icon icon="eye" />
                    </b-button>
                    <b-button
                        v-if="isHistoryItem"
                        :disabled="editDisabled"
                        class="px-1"
                        title="Edit attributes"
                        size="sm"
                        variant="link"
                        @click.stop="onEdit">
                        <icon icon="pen" />
                    </b-button>
                    <b-button
                        v-if="isHistoryItem && !item.deleted"
                        class="px-1"
                        title="Delete"
                        size="sm"
                        variant="link"
                        :disabled="item.purged"
                        @click.stop="$emit('delete', item)">
                        <icon icon="trash" />
                    </b-button>
                    <b-button
                        v-if="isHistoryItem && item.deleted"
                        class="px-1"
                        title="Undelete"
                        size="sm"
                        variant="link"
                        :disabled="item.purged"
                        @click.stop="$emit('undelete', item)">
                        <icon icon="trash-restore" />
                    </b-button>
                    <b-button
                        v-if="isHistoryItem && !item.visible"
                        class="px-1"
                        title="Unhide"
                        size="sm"
                        variant="link"
                        @click.stop="$emit('unhide', item)">
                        <icon icon="unlock" />
                    </b-button>
                </span>
            </div>
        </div>
        <!-- collections are not expandable, so we only need the DatasetDetails component here -->
        <div class="detail-animation-wrapper" :class="expandDataset ? '' : 'collapsed'">
            <DatasetDetails v-if="expandDataset" @edit="onEdit" :dataset="item" />
        </div>
    </div>
</template>

<script>
import { backboneRoute, useGalaxy, iframeRedirect } from "components/plugins/legacyNavigation";
import { Nametag } from "components/Nametags";
import CollectionDescription from "./Collection/CollectionDescription";
import DatasetDetails from "./Dataset/DatasetDetails";
import STATES from "./contentStates";

export default {
    components: {
        CollectionDescription,
        DatasetDetails,
        Nametag,
    },
    props: {
        expandDataset: { type: Boolean, required: true },
        item: { type: Object, required: true },
        id: { type: Number, required: true },
        isDataset: { type: Boolean, default: true },
        isHistoryItem: { type: Boolean, default: true },
        name: { type: String, required: true },
        selected: { type: Boolean, default: false },
        selectable: { type: Boolean, default: false },
    },
    computed: {
        contentId() {
            return `dataset-${this.item.id}`;
        },
        contentCls() {
            const status = this.contentState && this.contentState.status;
            if (this.selected) {
                return "alert-info";
            } else if (!status) {
                return `alert-success`;
            } else {
                return `alert-${status}`;
            }
        },
        contentState() {
            return STATES[this.state] && STATES[this.state];
        },
        displayButtonTitle() {
            if (this.item.purged) {
                return "Cannot display datasets removed from disk.";
            }
            if (this.displayDisabled) {
                return "This dataset is not yet viewable.";
            }
            return "Display";
        },
        displayDisabled() {
            return this.item.purged || ["discarded", "new", "upload"].includes(this.state);
        },
        editButtonTitle() {
            if (this.item.purged) {
                return "Cannot edit attributes of datasets removed from disk.";
            }
            if (this.editDisabled) {
                return "This dataset is not yet editable.";
            }
            return "Edit Attributes";
        },
        editDisabled() {
            return (
                this.item.purged || ["discarded", "new", "upload", "queued", "running", "waiting"].includes(this.state)
            );
        },
        hasStateIcon() {
            return this.contentState && this.contentState.icon;
        },
        state() {
            if (this.item.job_state_summary) {
                for (const key of ["error", "failed", "paused", "upload", "running"]) {
                    if (this.item.job_state_summary[key] > 0) {
                        return key;
                    }
                }
                return "ok";
            } else {
                return this.item.state;
            }
        },
    },
    methods: {
        onDragStart(evt) {
            evt.dataTransfer.dropEffect = "move";
            evt.dataTransfer.effectAllowed = "move";
            evt.dataTransfer.setData("text", JSON.stringify([this.item]));
        },
        onDisplay() {
            const id = this.item.id;
            useGalaxy((Galaxy) => {
                if (Galaxy.frame && Galaxy.frame.active) {
                    Galaxy.frame.addDataset(id);
                } else {
                    iframeRedirect(`datasets/${id}/display/?preview=True`);
                }
            });
        },
        onEdit() {
            if (this.item.collection_type) {
                backboneRoute(`collection/edit/${this.item.id}`);
            } else {
                backboneRoute("datasets/edit", { dataset_id: this.item.id });
            }
        },
        onClick() {
            if (this.isDataset) {
                this.$emit("update:expand-dataset", !this.expandDataset);
            } else {
                this.$emit("view-collection", this.item, this.name);
            }
        },
    },
};
</script>
<style>
.content-item:hover {
    filter: brightness(105%);
}
.content-item {
    .name {
        word-break: break-all;
    }
}
.detail-animation-wrapper {
    overflow: hidden;
    transition: max-height 0.2s ease-out;
    height: auto;
    max-height: 400px;
}
.detail-animation-wrapper.collapsed {
    max-height: 0;
}
</style>
