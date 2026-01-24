"""
Cloud Monitoring Dashboard Configuration for InfinityAI.Pro
"""

dashboard_config = {
    "displayName": "InfinityAI.Pro - Production Dashboard",
    "mosaicLayout": {
        "columns": 12,
        "tiles": [
            {
                "width": 6,
                "height": 4,
                "widget": {
                    "title": "Engine C - Response Time (P95)",
                    "xyChart": {
                        "dataSets": [{
                            "timeSeriesQuery": {
                                "timeSeriesFilter": {
                                    "filter": 'resource.type="cloud_run_revision" AND resource.labels.service_name="engine-c"',
                                    "aggregation": {
                                        "alignmentPeriod": "60s",
                                        "perSeriesAligner": "ALIGN_DELTA",
                                        "crossSeriesReducer": "REDUCE_PERCENTILE_95"
                                    }
                                }
                            }
                        }]
                    }
                }
            },
            {
                "width": 6,
                "height": 4,
                "widget": {
                    "title": "All Services - Error Rate",
                    "xyChart": {
                        "dataSets": [{
                            "timeSeriesQuery": {
                                "timeSeriesFilter": {
                                    "filter": 'resource.type="cloud_run_revision"',
                                    "aggregation": {
                                        "alignmentPeriod": "60s",
                                        "perSeriesAligner": "ALIGN_RATE"
                                    }
                                }
                            }
                        }]
                    }
                }
            },
            {
                "width": 4,
                "height": 4,
                "widget": {
                    "title": "Active Instances",
                    "xyChart": {
                        "dataSets": [{
                            "timeSeriesQuery": {
                                "timeSeriesFilter": {
                                    "filter": 'resource.type="cloud_run_revision"',
                                    "aggregation": {
                                        "alignmentPeriod": "60s",
                                        "perSeriesAligner": "ALIGN_MEAN"
                                    }
                                }
                            }
                        }]
                    }
                }
            }
        ]
    }
}

import json
print(json.dumps(dashboard_config, indent=2))
