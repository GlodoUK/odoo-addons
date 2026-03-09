import {GraphModel} from "@web/views/graph/graph_model";
import {patch} from "@web/core/utils/patch";

patch(GraphModel.prototype, {
    _getProcessedDataPoints() {
        if (this.metaData.mode !== "bar") return super._getProcessedDataPoints();
        // This minimal hack prevents hard overwriting _getProcessedDataPoints
        this.metaData.mode = "line";
        const result = super._getProcessedDataPoints();
        this.metaData.mode = "bar";
        return result;
    },

    _prepareData(forceUseAllDataPoints) {
        const result = super._prepareData(forceUseAllDataPoints);
        if (this.metaData.mode !== "bar") return result;
        this.data.datasets = this.data.datasets.filter((ds) => ds.data.some(Boolean));
        this.lineOverlayDataset = this._getLineOverlayDataset();
        return result;
    },
});
