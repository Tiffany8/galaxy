<template>
    <span class="zoom-control float-right btn-group-horizontal">
        <b-button
            role="button"
            class="fa fa-minus"
            title="Zoom Out"
            size="sm"
            aria-label="Zoom Out"
            v-b-tooltip.hover
            @click="onZoomOut" />
        <b-button
            role="button"
            class="zoom-reset"
            variant="light"
            title="Reset Zoom Level"
            size="sm"
            aria-label="Reset Zoom Level"
            v-b-tooltip.hover
            @click="onZoomReset">
            {{ this.zoomPercentage }}%
        </b-button>
        <b-button
            role="button"
            class="fa fa-plus"
            title="Zoom In"
            size="sm"
            aria-label="Zoom In"
            v-b-tooltip.hover
            @click="onZoomIn" />
    </span>
</template>

<script>
import Vue from "vue";
import BootstrapVue from "bootstrap-vue";
import { zoomLevels, defaultZoomLevel } from "./modules/canvas";

Vue.use(BootstrapVue);

export default {
    props: {
        zoomLevel: {
            type: Number,
            required: true,
        },
    },
    data() {
        return {
            zoomDefault: defaultZoomLevel,
        };
    },
    computed: {
        zoomPercentage() {
            return Math.floor(zoomLevels[this.zoomLevel] * 100);
        },
    },
    methods: {
        onZoomIn() {
            this.$emit("onZoom", this.zoomLevel + 1);
        },
        onZoomOut() {
            this.$emit("onZoom", this.zoomLevel - 1);
        },
        onZoomReset() {
            this.$emit("onZoom", this.zoomDefault);
        },
    },
};
</script>

<style scoped>
.zoom-reset {
    width: 4rem;
}
.zoom-control {
    position: absolute;
    left: 1rem;
    bottom: 1rem;
    cursor: pointer;
    z-index: 1002;
}
</style>
