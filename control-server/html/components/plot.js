app.component('data-plot', {
    template:
    /*html*/
`
<div class="plot-div">
    <div class="chart-heading">
        <h3>{{ chart_title }}</h3>
        Legend:&nbsp;
        <span v-for="station in stations" :style="{ color: station.color}">
            {{ station.name }}&nbsp;&nbsp;
        </span>
    </div>
    <div class="chart-container" style="position: relative; height:75%;">
        <canvas class="plot" :id="chart_id"></canvas>
    </div>
</div>
`,
    props: {
        sensor_data: {
            type: Object,
            required: true
        },
        data_point: {
            type: String,
            required: true
        }
    },
    data() {
        return {
            sensorDataChart: null,
            plotColors: [
                '#e6194b',
                '#3cb44b',
                '#ffe119',
                '#4363d8',
                '#f58231',
                '#911eb4',
                '#46f0f0',
                '#f032e6',
                '#bcf60c',
                '#fabebe',
                '#008080',
                '#e6beff',
                '#9a6324',
                '#fffac8',
                '#800000',
                '#aaffc3',
                '#808000',
                '#ffd8b1',
                '#000075',
                '#808080'
            ],
            stations: []
        }
    },
    methods: {
        /////////////////////////////////////
        // UTILITY FUNCTIONS

        // Compute a string with min/max/average on the given array of (x, y) points
        computeStats(sampleArray) {
            var minY = Number.MAX_SAFE_INTEGER, maxY = 0, avgY = 0;       
            var prevX = 0;
            sampleArray.forEach(function (point, index) {
                if (point.y < minY){
                    minY = point.y;
                }
                if (point.y > maxY) {
                    maxY = point.y;
                }
                if (prevX > 0) {
                    avgY = avgY + point.y * (point.x - prevX); // avg is weighted: samples with a longer period weight more
                }
                prevX = point.x;
            });
            avgY = avgY / (prevX - sampleArray[0].x);
            return "min: " + minY + ", max: " + maxY + ", avg: " + Math.floor(avgY);
        },
        plotData(sensorData) {
            // Response is e.g.: {"0": [{"time": 1608415319, "temperature": 69, "humidity": 40},
            //                          {"time": 1608415379, "temperature": 70, "humidity": 39}],
            //                    "1": [{"time": 1608415319, "temperature": 70, "humidity": 41},
            //                          {"time": 1608415379, "temperature": 69, "humidity": 42}]}
   
            var maxSamples = this.hoursToShow * 60;
    
            var nowSec = Math.round(Date.now() / 1000);
            var oldestTime = nowSec - maxSamples * 60;
    
            if (maxSamples <= 360) {
                this.sensorDataChart.options.scales.xAxes[0].time.stepSize = 15;
            } else if (maxSamples <= 720) {
                this.sensorDataChart.options.scales.xAxes[0].time.stepSize = 30;
            } else {
                this.sensorDataChart.options.scales.xAxes[0].time.stepSize = 60;
            }
            
            // Add point to analog chart
            // check if the property/key is defined in the object itself, not in parent
            for (stationId in this.sensor_data) {
                if (this.sensor_data.hasOwnProperty(stationId)) {
                    stationId = parseInt(stationId);
                    sensorData = this.sensor_data[stationId]
                    var dataSet = this.getDataSet(stationId);
                    if (dataSet != null) {
                        dataSet.data = []
                        for (var i = 0; i < sensorData.length; i++) {
                            dataPoint = sensorData[i]
                            dataSet.data.push({x: new Date(parseInt(dataPoint.time) * 1000), y: parseFloat(dataPoint[this.data_point])});
                            // Limit its length to maxSamples
                            dataSet.data.splice(0, dataSet.data.length - maxSamples);
                        }
                    }
                }
            }
    
            this.sensorDataChart.update();
        },
        getDataSet(stationId) {
            for (dataSet of this.sensorDataChart.data.datasets) {
                if (dataSet.stationId == stationId) {
                    return dataSet;
                }
            }

            return this.addDataSet(stationId);
        },
        addDataSet(stationId) {
            var newIndex = this.sensorDataChart.data.datasets.length;
            dataSet = {
                label: 'Station ' + stationId,
                backgroundColor: 'rgb(0,0,0,0)',
                borderColor: this.plotColors[newIndex % this.plotColors.length],
                data: [],
                showLine:true,
                cubicInterpolationMode: 'monotone',
                stationId: stationId
            }
            this.sensorDataChart.data.datasets.push(dataSet);
            this.stations.push({'name': dataSet.label, 'color': dataSet.borderColor});
            return this.sensorDataChart.data.datasets[newIndex];
        }
    },
    computed: {
        chart_title() {
            if (this.data_point == 'temperature') {
                return 'Station Temperatures'
            }

            if (this.data_point == 'humidity') {
                return 'Station Humidities'
            }

            if (this.data_point == 'vcc') {
                return 'Station Supply Voltages'
            }

            return 'Station ' + this.data_point;
        },
        chart_id() {
            return 'plot-' + this.data_point;
        }
    },
    mounted() {
        this.sensorDataChart = new Chart(document.getElementById(this.chart_id), {
            // The type of chart we want to create
            type: 'scatter',
        
            // The data for our dataset
            data: {
              datasets: []
            },
        
            // Configuration options go here
            options: {
              maintainAspectRatio: false,
              title: {
                display: false
              },
              legend: {
                display: false
              },
              scales: {
                xAxes: [{
                  id:"x-axis",
                  type:"time",
                  time: {
                    unit: 'minute',
                    stepSize: 30
                  },
                  ticks: {
                    minRotation:0,
                    maxRotation:0
                  }
                }],
                yAxes: [{
                  ticks: {
                    beginAtZero:false
                  }
                }]
              },
              tooltips: {
                intersect: false
              },
              animation: {
                duration: 0
              },
              hover: {
                animationDuration: 0
              },
              
              // Zoom plugin options
              plugins: {
                zoom: {
                  pan: {
                    enabled: true,
                    mode: 'y',
                  },
                  zoom: {
                    enabled: true,
                    mode: 'y',
                  }
                }
              },
              
              onClick: function() {this.resetZoom()}
            }
        
        })
        this.plotData(this.chartData);
    }
});
