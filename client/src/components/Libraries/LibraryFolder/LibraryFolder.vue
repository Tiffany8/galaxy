<template>
    <CurrentUser v-slot="{ user }">
        <div>
            <FolderTopBar
                @updateSearch="updateSearchValue($event)"
                @refreshTable="refreshTable"
                @refreshTableContent="refreshTableContent"
                @fetchFolderContents="fetchFolderContents($event)"
                @deleteFromTable="deleteFromTable"
                @setBusy="setBusy($event)"
                @newFolder="newFolder"
                :folder-contents="folderContents"
                :include_deleted="include_deleted"
                :folder_id="current_folder_id"
                :selected="selected"
                :metadata="folder_metadata"
                :unselected="unselected"
                :is-all-selected-mode="isAllSelectedMode" />

            <b-table
                id="folder_list_body"
                striped
                hover
                :busy.sync="isBusy"
                :fields="fields"
                :items="folderContents"
                :per-page="perPage"
                selectable
                no-select-on-click
                @row-clicked="onRowClick"
                ref="folder_content_table"
                show-empty>
                <template v-slot:empty>
                    <div v-if="isBusy" class="text-center my-2">
                        <b-spinner class="align-middle"></b-spinner>
                        <strong>Loading...</strong>
                    </div>
                    <div v-else class="empty-folder-message">
                        This folder is either empty or you do not have proper access permissions to see the contents. If
                        you expected something to show up please consult the
                        <a href="https://galaxyproject.org/data-libraries/#permissions" target="_blank">
                            library security wikipage
                        </a>
                    </div>
                </template>
                <template v-slot:head(selected)="">
                    <font-awesome-icon
                        v-if="isAllSelectedMode && !isAllSelectedOnPage()"
                        @click="toggleSelect"
                        class="select-checkbox cursor-pointer"
                        size="lg"
                        title="Check to select all datasets"
                        icon="minus-square" />
                    <font-awesome-icon
                        v-else
                        @click="toggleSelect"
                        class="select-checkbox cursor-pointer"
                        size="lg"
                        title="Check to select all datasets"
                        :icon="isAllSelectedOnPage() ? ['far', 'check-square'] : ['far', 'square']" />
                </template>
                <template v-slot:cell(selected)="row">
                    <font-awesome-icon
                        class="select-checkbox lib-folder-checkbox"
                        size="lg"
                        v-if="!row.item.isNewFolder && !row.item.deleted"
                        :icon="row.rowSelected ? ['far', 'check-square'] : ['far', 'square']" />
                </template>
                <!-- Name -->
                <template v-slot:cell(name)="row">
                    <div v-if="row.item.editMode">
                        <textarea
                            v-if="row.item.isNewFolder"
                            class="form-control"
                            name="input_folder_name"
                            :ref="'name' + row.item.id"
                            v-model="row.item.name"
                            rows="3" />
                        <textarea
                            v-else
                            class="form-control"
                            :ref="'name' + row.item.id"
                            :value="row.item.name"
                            rows="3" />
                    </div>
                    <div v-else-if="!row.item.deleted">
                        <b-link
                            v-if="row.item.type === 'folder'"
                            :to="{ name: `LibraryFolder`, params: { folder_id: `${row.item.id}` } }"
                            >{{ row.item.name }}</b-link
                        >

                        <b-link
                            v-else
                            :to="{
                                name: `LibraryDataset`,
                                params: { folder_id: folder_id, dataset_id: `${row.item.id}` },
                            }"
                            >{{ row.item.name }}</b-link
                        >
                    </div>
                    <!-- Deleted Item-->
                    <div v-else>
                        <div class="deleted-item">{{ row.item.name }}</div>
                    </div>
                </template>

                <!-- Description -->
                <template v-slot:cell(message)="row">
                    <div v-if="row.item.editMode">
                        <textarea
                            v-if="row.item.isNewFolder"
                            class="form-control input_folder_description"
                            :ref="'description' + row.item.id"
                            v-model="row.item.description"
                            rows="3"></textarea>
                        <textarea
                            v-else
                            class="form-control input_folder_description"
                            :ref="'description' + row.item.id"
                            :value="row.item.description"
                            rows="3"></textarea>
                    </div>
                    <div v-else>
                        <div class="description-field" v-if="getMessage(row.item)">
                            <div
                                v-if="
                                    getMessage(row.item).length > maxDescriptionLength &&
                                    !expandedMessage.includes(row.item.id)
                                ">
                                <span
                                    class="shrinked-description"
                                    :title="getMessage(row.item)"
                                    v-html="linkify(getMessage(row.item).substring(0, maxDescriptionLength))">
                                </span>
                                <span :title="getMessage(row.item)"> ...</span>
                                <a class="more-text-btn" @click="expandMessage(row.item)" href="javascript:void(0)"
                                    >(more)</a
                                >
                            </div>
                            <div v-else v-html="linkify(getMessage(row.item))"></div>
                        </div>
                    </div>
                </template>
                <template v-slot:cell(type_icon)="row">
                    <font-awesome-icon v-if="row.item.type === 'folder'" :icon="['far', 'folder']" title="Folder" />
                    <font-awesome-icon v-else-if="row.item.type === 'file'" title="Dataset" :icon="['far', 'file']" />
                </template>
                <template v-slot:cell(type)="row">
                    <div v-if="row.item.type === 'folder'">{{ row.item.type }}</div>
                    <div v-else-if="row.item.type === 'file'">{{ row.item.file_ext }}</div>
                </template>
                <template v-slot:cell(raw_size)="row">
                    <div v-if="row.item.type === 'file'" v-html="bytesToString(row.item.raw_size)"></div>
                </template>
                <template v-slot:cell(state)="row">
                    <div v-if="row.item.state != 'ok'">
                        {{ row.item.state }}
                    </div>
                </template>
                <template v-slot:cell(update_time)="row">
                    <UtcDate
                        v-if="row.item.update_time"
                        :date="row.item.update_time"
                        custom-format="'YYYY-MM-DD- HH:mm a'"
                        mode="elapsed" />
                </template>
                <template v-slot:cell(is_unrestricted)="row">
                    <font-awesome-icon v-if="row.item.is_unrestricted" title="Unrestricted dataset" icon="globe" />
                    <font-awesome-icon
                        v-else-if="row.item.deleted"
                        title="Marked deleted"
                        icon="ban"></font-awesome-icon>
                    <font-awesome-icon v-else-if="row.item.is_private" title="Private dataset" icon="key" />
                    <font-awesome-icon
                        v-else-if="row.item.is_private === false && row.item.is_unrestricted === false"
                        title="Restricted dataset"
                        icon="shield-alt" />
                </template>

                <template v-slot:cell(buttons)="row">
                    <div v-if="row.item.editMode">
                        <button
                            @click="row.item.isNewFolder ? createNewFolder(row.item) : saveChanges(row.item)"
                            class="primary-button btn-sm permission_folder_btn save_folder_btn"
                            :title="'save ' + row.item.name">
                            <font-awesome-icon :icon="['far', 'save']" />
                            Save
                        </button>
                        <button
                            class="primary-button btn-sm permission_folder_btn"
                            title="Discard Changes"
                            @click="toggleEditMode(row.item)">
                            <font-awesome-icon :icon="['fas', 'times']" />
                            Cancel
                        </button>
                    </div>
                    <div v-else>
                        <b-button
                            v-if="row.item.can_manage && !row.item.deleted && row.item.type === 'folder'"
                            @click="toggleEditMode(row.item)"
                            data-toggle="tooltip"
                            data-placement="top"
                            size="sm"
                            class="lib-btn permission_folder_btn edit_folder_btn"
                            :title="'Edit ' + row.item.name">
                            <font-awesome-icon icon="pencil-alt" />
                            Edit
                        </b-button>
                        <b-button
                            v-if="user.is_admin"
                            size="sm"
                            class="lib-btn permission_lib_btn"
                            :title="`Permissions of ${row.item.name}`"
                            :to="{ path: `${navigateToPermission(row.item)}` }">
                            <font-awesome-icon icon="users" />
                            Manage
                        </b-button>
                        <button
                            @click="undelete(row.item, folder_id)"
                            v-if="row.item.deleted"
                            :title="'Undelete ' + row.item.name"
                            class="lib-btn primary-button btn-sm undelete_dataset_btn"
                            type="button">
                            <font-awesome-icon icon="unlock" />
                            Undelete
                        </button>
                    </div>
                </template>
            </b-table>
            <!-- hide pagination if the table is loading-->
            <b-container>
                <b-row align-v="center" class="justify-content-md-center">
                    <b-col md="auto">
                        <div v-if="isBusy">
                            <b-spinner small type="grow"></b-spinner>
                            <b-spinner small type="grow"></b-spinner>
                            <b-spinner small type="grow"></b-spinner>
                        </div>
                        <b-pagination
                            v-else
                            :value="currentPage"
                            :total-rows="total_rows"
                            :per-page="perPage"
                            @input="changePage"
                            aria-controls="folder_list_body">
                        </b-pagination>
                    </b-col>

                    <b-col cols="1.5">
                        <table>
                            <tr>
                                <td class="m-0 p-0">
                                    <b-form-input
                                        class="pagination-input-field"
                                        id="paginationPerPage"
                                        autocomplete="off"
                                        type="number"
                                        v-model="perPage" />
                                </td>
                                <td class="text-muted ml-1 paginator-text">
                                    <span class="pagination-total-pages-text">per page, {{ total_rows }} total</span>
                                </td>
                            </tr>
                        </table>
                    </b-col>
                </b-row>
            </b-container>
        </div>
    </CurrentUser>
</template>

<script>
import Vue from "vue";
import { getAppRoot } from "onload/loadConfig";
import UtcDate from "components/UtcDate";
import BootstrapVue from "bootstrap-vue";
import { Services } from "./services";
import Utils from "utils/utils";
import linkifyHtml from "linkify-html";
import { fields } from "./table-fields";
import { Toast } from "ui/toast";
import FolderTopBar from "./TopToolbar/FolderTopBar";
import { initFolderTableIcons } from "components/Libraries/icons";
import { MAX_DESCRIPTION_LENGTH, DEFAULT_PER_PAGE } from "components/Libraries/library-utils";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";
import CurrentUser from "components/providers/CurrentUser";

initFolderTableIcons();

Vue.use(BootstrapVue);

function initialFolderState() {
    return {
        selected: [],
        unselected: [],
        expandedMessage: [],
        folderContents: [],
        include_deleted: false,
        search_text: "",
        isAllSelectedMode: false,
    };
}
export default {
    props: {
        folder_id: {
            type: String,
            required: true,
        },
        page: {
            type: Number,
            default: 1,
            required: false,
        },
    },
    components: {
        FolderTopBar,
        UtcDate,
        FontAwesomeIcon,
        CurrentUser,
    },
    data() {
        return {
            ...initialFolderState(),
            ...{
                currentPage: null,
                current_folder_id: null,
                error: null,
                isBusy: false,
                folder_metadata: {},
                fields: fields,
                selectMode: "multi",
                perPage: DEFAULT_PER_PAGE,
                maxDescriptionLength: MAX_DESCRIPTION_LENGTH,
                total_rows: 0,
                root: getAppRoot(),
            },
        };
    },
    created() {
        this.services = new Services({ root: this.root });
        this.getFolder(this.folder_id, this.page);
    },
    methods: {
        getFolder(folder_id, page) {
            this.current_folder_id = folder_id;
            this.currentPage = page;
            this.resetData();
            this.fetchFolderContents(this.include_deleted);
        },
        resetData() {
            const data = initialFolderState();
            Object.keys(data).forEach((k) => (this[k] = data[k]));
        },
        fetchFolderContents(include_deleted = false) {
            this.include_deleted = include_deleted;
            this.setBusy(true);
            this.services
                .getFolderContents(
                    this.current_folder_id,
                    include_deleted,
                    this.perPage,
                    (this.currentPage - 1) * this.perPage,
                    this.search_text
                )
                .then((response) => {
                    this.folderContents = response.folder_contents;
                    this.folder_metadata = response.metadata;
                    this.total_rows = response.metadata.total_rows;
                    if (this.isAllSelectedMode) {
                        this.selected = [];
                        Vue.nextTick(() => {
                            this.selectAllRenderedRows();
                        });
                    } else if (this.selected.length > 0) {
                        Vue.nextTick(() => {
                            this.selected.forEach((row) => this.select_unselect_row_by_id(row.id));
                        });
                    }
                    this.setBusy(false);
                })
                .catch((error) => {
                    this.error = error;
                });
        },
        updateSearchValue(value) {
            this.search_text = value;
            this.folderContents = [];
            this.fetchFolderContents(this.include_deleted);
        },
        selectAllRenderedRows() {
            this.$refs.folder_content_table.items.forEach((row, index) => {
                if (!row.isNewFolder && !row.deleted && !this.unselected.some((unsel) => unsel.id === row.id)) {
                    this.select_unselect_row(index);
                    if (!this.selected.some((selectedItem) => selectedItem.id === row.id)) {
                        this.selected.push(row);
                    }
                }
            });
        },
        clearRenderedSelectedRows() {
            this.$refs.folder_content_table.clearSelected();
            this.selected = [];
        },
        refreshTable() {
            this.$refs.folder_content_table.refresh();
        },
        refreshTableContent() {
            this.fetchFolderContents(this.include_deleted);
        },
        deleteFromTable(deletedItem) {
            this.folderContents = this.folderContents.filter((element) => {
                if (element.id !== deletedItem.id) {
                    return element;
                }
            });
        },
        isAllSelectedOnPage() {
            if (!this.$refs.folder_content_table) {
                return false;
            }

            // Since we cannot select new folders, toggle should clear all if all rows match, expect new folders
            let unselectable = 0;

            this.$refs.folder_content_table.computedItems.forEach((row) => {
                if (row.isNewFolder || row.deleted) {
                    unselectable++;
                }
            });

            return this.selected.length + unselectable === this.$refs.folder_content_table.computedItems.length;
        },
        toggleSelect() {
            this.unselected = [];
            if (this.isAllSelectedOnPage()) {
                this.isAllSelectedMode = false;
                this.clearRenderedSelectedRows();
            } else {
                this.isAllSelectedMode = true;
                this.selectAllRenderedRows();
            }
        },
        newFolder() {
            this.folderContents.unshift({
                editMode: true,
                isNewFolder: true,
                type: "folder",
                name: "",
                description: "",
            });
            this.refreshTable();
        },
        onRowClick(row, index, event) {
            // check if exists
            const selected_array_index = this.selected.findIndex((item) => item.id === row.id);
            if (selected_array_index > -1) {
                this.selected.splice(selected_array_index, 1);
                this.select_unselect_row(index, true);
                if (this.isAllSelectedMode) {
                    this.unselected.push(row);
                    if (this.total_rows === this.unselected.length) {
                        // if user presses `selectAll` and unselects everything manually
                        this.isAllSelectedMode = false;
                        this.unselected = [];
                    }
                }
            } else {
                if (!row.isNewFolder && !row.deleted) {
                    this.select_unselect_row(index);
                    this.selected.push(row);
                }
            }
        },
        select_unselect_row_by_id(id, unselect = false) {
            const index = this.$refs.folder_content_table.items.findIndex((row) => row.id === id);
            this.select_unselect_row(index, unselect);
        },
        select_unselect_row(index, unselect = false) {
            if (unselect) {
                this.$refs.folder_content_table.unselectRow(index);
            } else {
                this.$refs.folder_content_table.selectRow(index);
            }
        },
        bytesToString(raw_size) {
            return Utils.bytesToString(raw_size);
        },
        navigateToPermission(element) {
            if (element.type === "file") {
                return `/folders/${this.folder_id}/dataset/${element.id}/permissions`;
            } else if (element.type === "folder") {
                return `/folders/${element.id}/permissions`;
            }
        },
        getMessage(element) {
            if (element.type === "file") {
                return element.message;
            } else if (element.type === "folder") {
                return element.description;
            }
        },
        expandMessage(element) {
            this.expandedMessage.push(element.id);
        },
        setBusy(value) {
            this.isBusy = value;
        },
        linkify(raw_text) {
            return linkifyHtml(raw_text);
        },
        toggleEditMode(item) {
            item.editMode = !item.editMode;
            this.folderContents = this.folderContents.filter((item) => {
                if (!item.isNewFolder) {
                    return item;
                }
            });
            this.refreshTable();
        },
        createNewFolder: function (folder) {
            if (!folder.name) {
                Toast.error("Folder's name is missing.");
            } else if (folder.name.length < 3) {
                Toast.warning("Folder name has to be at least 3 characters long.");
            } else {
                this.services.newFolder(
                    {
                        parent_id: this.current_folder_id,
                        name: folder.name,
                        description: folder.description,
                    },
                    (resp) => {
                        folder.id = resp.id;
                        folder.update_time = resp.update_time;
                        folder.editMode = false;
                        folder.can_manage = true;
                        folder.isNewFolder = false;

                        this.refreshTable();
                        Toast.success("Folder created.");
                    },
                    () => {
                        Toast.error("An error occurred.");
                    }
                );
            }
        },
        undelete: function (element, parent_folder) {
            const onError = (response) => {
                const message = `${element.type === "folder" ? "Folder" : "Dataset"}`;
                if (typeof response.responseJSON !== "undefined") {
                    Toast.error(`${message} was not undeleted. ${response.responseJSON.err_msg}`);
                } else {
                    Toast.error(`An error occurred! ${message} was not undeleted. Please try again.`);
                }
            };
            if (element.type === "folder") {
                this.services.undeleteFolder(
                    element,
                    (response) => {
                        element.deleted = response.deleted;
                        this.refreshTable();
                        Toast.success("Folder undeleted.");
                    },
                    onError
                );
            } else {
                this.services.undeleteDataset(
                    element,
                    (response) => {
                        element.deleted = response.deleted;
                        this.refreshTable();
                        Toast.success("Dataset undeleted. Click here to see it.", "", {
                            onclick: function () {
                                window.location = `${getAppRoot()}libraries/folders/${parent_folder}/dataset/${
                                    element.id
                                }`;
                            },
                        });
                    },
                    onError
                );
            }
        },
        changePage(page) {
            this.$router.push({ name: `LibraryFolder`, params: { folder_id: this.folder_id, page: page } });
        },

        /*
         Former Backbone code, adopted to work with Vue
        */
        saveChanges(folder) {
            let is_changed = false;
            const new_name = this.$refs[`name${folder.id}`].value;
            if (new_name && new_name !== folder.name) {
                if (new_name.length > 2) {
                    folder.name = new_name;
                    is_changed = true;
                } else {
                    Toast.warning("Folder name has to be at least 3 characters long.");
                    return;
                }
            }
            const new_description = this.$refs[`description${folder.id}`].value;
            if (typeof new_description !== "undefined" && new_description !== folder.description) {
                folder.description = new_description;
                is_changed = true;
            }
            if (is_changed) {
                this.services.updateFolder(
                    folder,
                    () => {
                        Toast.success("Changes to folder saved.");
                        folder.editMode = false;
                        this.refreshTable();
                    },
                    (error) => {
                        if (error.data && error.data.err_msg) {
                            Toast.error(error.data.err_msg);
                        } else {
                            Toast.error("An error occurred while attempting to update the folder.");
                        }
                    }
                );
            } else {
                Toast.info("Nothing has changed.");
            }
        },
    },
    watch: {
        perPage: {
            handler: function (value) {
                this.fetchFolderContents(this.include_deleted);
            },
        },
    },
    beforeRouteUpdate(to, from, next) {
        this.getFolder(to.params.folder_id, to.params.page);
        next();
    },
};
</script>

<style scoped>
@import "library-folder-table.css";
</style>
