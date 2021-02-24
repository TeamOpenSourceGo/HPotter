const url = "http://localhost:8080/"
let myMap;
let iw;

let script = document.createElement('script');
script.src = "https://maps.googleapis.com/maps/api/js?key=YOURKEYHERE&callback=initMap"
script.async = true;

function initMap() {
  myMap = new google.maps.Map(document.getElementById('map'),
    { center: {lat: 0, lng: 0}, zoom: 2});
  iw = new google.maps.InfoWindow();

  oms = new OverlappingMarkerSpiderfier(myMap, {
    markersWontMove: true,
    markersWontHide: true,
    basicFormatEvents: true
  });
  fetchAllLocations();
}

document.head.appendChild(script);

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
   
  let information = new google.maps.InfoWindow({
    content: getContentHTML(node),
  });
 
  google.maps.event.addListener(marker, 'spider_click', function(e) {
    iw.setContent(getContentHTML(node));
    iw.open(myMap, marker);
  }); 
  oms.addMarker(marker); 

  return marker;
}

function createMarkers(edges) {
  let markers = [];
  if(Array.isArray(edges)) {
    markers = edges.map(edge => createPointMarker(edge.node)); 
  } else {
    console.log("Invalid input type.  Edges must be an array.");
  }
  return markers;
}

function process(data) {
  if(data.allConnections && data.allConnections.edges.length > 0) {
    const markers = createMarkers(data.allConnections.edges);
    const properties = {
      imagePath: './images/m',
      maxZoom: 15
    };

    new MarkerClusterer(myMap, markers, properties);
  }
}

function fetchAllLocations() {
  let params = {
    method: "POST",
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ query: '{allConnections{edges{node{sourceAddress sourcePort destinationAddress destinationPort latitude longitude createdAt}}}}'}) 
  };
  
  fetch(url, params)
    .then(data => {
      return data.json();
    })
    .then(resp => {
      if(resp && resp.data) {
        process(resp.data); 
      } else {
        console.log("Failed to load data from server.");
      } 
    })
    .catch(error => 
      console.log(error)
    );
}
