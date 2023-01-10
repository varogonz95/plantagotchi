import PropTypes from 'prop-types';
import ReactApexChart from 'react-apexcharts';
// @mui
import { Card, CardHeader, Box } from '@mui/material';
// components
import { useChart } from '../../../components/chart';

// ----------------------------------------------------------------------

SensorReadingsChart.propTypes = {
    title: PropTypes.string,
    subheader: PropTypes.string,
    chartData: PropTypes.array.isRequired,
    chartLabels: PropTypes.arrayOf(PropTypes.any).isRequired,
};

export default function SensorReadingsChart({ title, subheader, chartLabels, chartData, ...other }) {
    const chartOptions = useChart({
        fill: { type: 'gradient' },
        stroke: { width: 2 },
        labels: chartLabels,
        xaxis: { type: 'datetime' },
        tooltip: {
            shared: true,
            intersect: false,
            y: {
                formatter: (y) => {
                    if (typeof y !== 'undefined') {
                        return y.toFixed(2);
                    }
                    return y;
                },
            },
        },
    });

    return (
        <Card {...other}>
            <CardHeader title={title} subheader={subheader} />

            <Box sx={{ p: 3, pb: 1 }} dir="ltr">
                <ReactApexChart type="area" series={[{data: chartData}]} options={chartOptions} height={364} />
            </Box>
        </Card>
    );
}
