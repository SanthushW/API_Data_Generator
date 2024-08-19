const fs = require('fs');

// Configuration
const numberOfTrains = 2; // Number of trains to simulate
const dataPointsPerTrain = 10; // Number of data points per train (e.g., 1440 for one per minute over 24 hours)
const latitudeRange = { min: 5.9200, max: 9.8300 }; // Latitude range for Sri Lanka
const longitudeRange = { min: 79.6500, max: 81.8700 }; // Longitude range for Sri Lanka
const startTime = new Date().getTime() - 24 * 60 * 60 * 1000; // Start time (24 hours ago)
const interval = 60 * 1000; // 1 minute intervals in milliseconds

// Function to generate random latitude and longitude within a specified range
function getRandomCoordinate(range) {
    return (Math.random() * (range.max - range.min) + range.min).toFixed(6);
}

// Function to generate GPS data for a train
function generateTrainData(trainId) {
    const data = [];

    for (let i = 0; i < dataPointsPerTrain; i++) {
        const timestamp = new Date(startTime + i * interval).toISOString();
        const latitude = getRandomCoordinate(latitudeRange);
        const longitude = getRandomCoordinate(longitudeRange);

        data.push({
            trainId,
            timestamp,
            latitude,
            longitude,
        });
    }

    return data;
}

// Generate data for all trains
const allTrainData = [];

for (let i = 1; i <= numberOfTrains; i++) {
    const trainData = generateTrainData(`Train_${i}`);
    allTrainData.push(...trainData);
}

// Write the data to a JSON file
fs.writeFileSync('trainLocationData.json', JSON.stringify(allTrainData, null, 2));

console.log('Train location data generated successfully!');
