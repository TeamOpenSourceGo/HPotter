const url = "http://localhost:8080/"

let myMap;
let iw;
let myMarkers = [];
let myMarkerClusterer;
let script = document.createElement('script');
script.src = "https://maps.googleapis.com/maps/api/js?key=YOURKEYHERE&callback=initMap"
script.async = true;

function initMap() {
  myMap = new google.maps.Map(document.getElementById('map'),
    { center: {lat: 0, lng: 0}, zoom: 3});
  iw = new google.maps.InfoWindow();

  oms = new OverlappingMarkerSpiderfier(myMap, {
    markersWontMove: true,
    markersWontHide: true,
    basicFormatEvents: true
  });
  fetchLocations();
  addCustomControls();
  addEventListeners();
}

document.head.appendChild(script);

function addCustomControls() {
  const dateDiv = document.getElementById("hp-date-picker");
  myMap.controls[google.maps.ControlPosition.TOP_RIGHT].push(dateDiv);

  const zoomToBounds = document.getElementById("hp-zoom-to-bounds");
  myMap.controls[google.maps.ControlPosition.RIGHT_TOP].push(zoomToBounds);
}

function addEventListeners() {

  const mapDiv = document.getElementById("date-submit");
  google.maps.event.addDomListener(mapDiv, "click", (e) => {
    e.preventDefault();
    let start = document.getElementById("startDate").value;
    let end = document.getElementById("endDate").value;
    if(start && end) {
      start = moment(start, "YYYY-MM-DD");
      end = moment(end, "YYYY-MM-DD");
    }
    fetchLocations(start, end);
  });

  const zoomToBounds = document.getElementById("hp-zoom-to-bounds");
  google.maps.event.addDomListener(zoomToBounds, "click", () => {
    const bounds = new google.maps.LatLngBounds();
    myMarkers.forEach(mark => bounds.extend(mark.position));
    myMap.fitBounds(bounds);
  });

}

function getContentHTML(node) {
  let content = "<div>"
  for(const key of Object.keys(node)) {
     if(node[key]) {
       content += `<div>${key.toUpperCase()}: ${node[key]}</div>`;
     }
  }

  content += "</div>";
  return content;
}

function createPointMarker(node) {
  let geom = new google.maps.LatLng(node.latitude, node.longitude);
  let marker = new google.maps.Marker({
    position: geom,
  });
 
  google.maps.event.addListener(marker, 'spider_click', function(e) {
    iw.setContent(getContentHTML(node));
    iw.open(myMap, marker);
  }); 
  oms.addMarker(marker); 

  return marker;
}

function filterByDate(edges, startDate, endDate) {
  if(!startDate || !endDate) {
    return edges;
  }

  return edges.filter(edge => {
      let createdAt = moment(edge.node.createdAt, "YYYY-MM-DD'T'hh:mm:ss");
      return createdAt.isSameOrAfter(startDate, 'day') && createdAt.isSameOrBefore(endDate, 'day');
  });
}

function createMarkers(edges) {
  if(Array.isArray(edges)) {
    myMarkers = edges.map(edge => createPointMarker(edge.node)); 
  } else {
    console.log("Invalid input type.  Edges must be an array.");
  }
}

function process(data, startDate, endDate) {
  if(data.allConnections && data.allConnections.edges.length > 0) {
    const edges = filterByDate(data.allConnections.edges, startDate, endDate);
    createMarkers(edges);
    const properties = {
      imagePath: './static/images/m',
      maxZoom: 15
    };

    myMarkerClusterer = new MarkerClusterer(myMap, myMarkers, properties);
  }
}

// Sets the map on all markers in the array.
function setMapOnAll(map) {
  for (let i = 0; i < myMarkers.length; i++) {
    myMarkers[i].setMap(map);
  }
}

// Removes the markers from the map
function clearMarkers() {
  setMapOnAll(null);
  if(myMarkerClusterer) {
    myMarkerClusterer.clearMarkers();
  }
  myMarkers = [];
}

/**
 * 
 * @param {Object} [startDate] Start Date moment date object
 * @param {Object} [endDate] End Date moment date object
 */
function fetchLocations(startDate, endDate) {
  let params = {
    method: "POST",
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ query: '{allConnections{edges{node{sourceAddress sourcePort destinationAddress destinationPort latitude longitude createdAt}}}}'}) 
  };
  
  clearMarkers();
  fetch(url, params)
    .then(data => {
      return data.json();
    })
    .then(resp => {
      if(resp && resp.data) {
        process(resp.data, startDate, endDate); 
      } else {
        console.log("Failed to load data from server.");
      } 
    })
    .catch(error => 
      console.log(error)
    );
}
