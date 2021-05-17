import React, { useState, useEffect} from 'react';
import { withRouter } from "react-router-dom";
const path = require('path');
require('dotenv').config({path: path.resolve(__dirname+'/.env')});

function get_url_domain(url) {
  const a = document.createElement('a');
         a.href = url;
  return a.hostname;
}
function sortByDate(dates) {
  let dates_sorted = dates.sort(function(a, b){
    let d1_split = a.date.split('/')
    let d1 = new Date(Number(d1_split[2]), Number(d1_split[1]) - 1, Number(d1_split[0]));
    let d2_split = b.date.split('/')
    let d2 = new Date(Number(d2_split[2]), Number(d2_split[1]) - 1, Number(d2_split[0]));
    return d2 - d1;
  });
  return dates_sorted
}

function Offers(props) {
  const [param, setParam] = useState(props);
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState("")
  const [timer, setTimer] = useState(0)
  const [timer_sec, setTimer_sec] = useState(0)
  const [timer_min, setTimer_min] = useState(0)

  useEffect(() => {
    fetchOffer()
  }, []);

  const fetchOffer = () => {
    switch (param.location.pathname) {
      case '/':
        fetch('/api/offers')
          .then(res => res.json())
          .then(list => {
            setResults(sortByDate(list))
          });
        break
      case '/fav':
        fetch('/api/offers/fav')
          .then(res => res.json())
          .then(list => {
            setResults(sortByDate(list))
          });
        break
    }
  }

  const updateOffer = (offer, name, val) => {
    offer = { ...offer, [name]: JSON.parse(val)};
    (async () => {
      const rawResponse = await fetch(`/api/update/${offer._id}`, {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(offer)
      });
      const content = await rawResponse.json();
      fetchOffer()
    })();
  }
  const handleTimer = () => {
    let time = setInterval(() => {
      setTimer((timer) => {
        if(timer === 60) {
          setTimer_min((timer_min) => timer_min + 1)
          setTimer(0)
          setTimer_sec(0)
        } else {
          if(timer === 30) {
            fetchOffer()
          }
          setTimer_sec(timer)
        }
        return (timer + 1)
      })
      
    }, 1000)
    return time
  }
  const refreshOffers = () => {
    let time = handleTimer()
    setLoading("loading")
    fetch("http://" + process.env.REACT_APP_DEFAULT_URL+":"+process.env.REACT_APP_DEFAULT_PORT, {
      mode: 'no-cors'
  })
    .then(res => {
      if(res) {
        setLoading("success");
        clearInterval(time)
        setTimer(0)
        setTimer_min(0)
        setTimer_sec(0)
      }
    })
    .catch(function(error) {
      console.log('Il y a eu un problème avec l\'opération fetch: ' + error.message);
    });
  }
  if(loading === "success") {
    console.log(timer_min
      .toLocaleString('en-US', {minimumIntegerDigits: 2, useGrouping: false})
      + " : "
      + timer_sec.toLocaleString('en-US', {minimumIntegerDigits: 2, useGrouping: false}))
  }
  return (
    <div className="App">
      <div className="top_container" >
        {param.location.pathname === "/" ? (<a className="navigate_link" href="/fav">Favorites</a>) : (<a className="navigate_link" href="/">Home</a>) }
        {loading === "loading"
        ? (<div className="refresh_loader">
            <p> Loading (~1mins): <br/>
              {timer_min
              .toLocaleString('en-US', {minimumIntegerDigits: 2, useGrouping: false})
              + " : "
              + timer_sec.toLocaleString('en-US', {minimumIntegerDigits: 2, useGrouping: false})}
            </p>
            <i className="fa fa-spinner fa-spin "></i>
          </div>)
        : (<button className="refresh_offers" onClick={() => refreshOffers()}>Refresh offers<i class="fa fa-refresh" aria-hidden="true"></i>{loading === "success" ? (<span className="message success">Offers Succesfully updated !</span>): null}</button>)}
      </div>
      <h1>
        {param.location.pathname === "/fav" ? "All favorites offers " : "All offers " }({results.length}) :
      </h1>
      <div class="cards_container">
        <div class="cards_container_header" >
          <h2>FAV</h2>
        </div>
        {results.length === 0 ? (<i className="fa fa-spinner fa-spin spinner"></i>) : null}
        {results.map((value, index) => {
           return (
              <div class="card" id-offers={value._id} is-readed={value.read === true? "true" : "false"} onClick={(e) => e.currentTarget.getAttribute("is-readed") === "false" ? updateOffer(value, "read", "true") : null}>
                  <div class="is_fav_container">
                    <label class="is_fav">
                      {value.is_fav === true ? (<input type="checkbox" defaultChecked onChange={(e) => updateOffer(value, "is_fav", e.currentTarget.checked)}></input>): (<input type="checkbox" onChange={(e) => updateOffer(value, "is_fav", e.currentTarget.checked)}></input>)}
                      <svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" viewBox="0 0 24 24" fill={value.is_fav === true ? "#0984e3" : "none"} stroke="#0984e3" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-heart"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path></svg>
                      
                    </label>
                  </div>
                  
                  <a class="card_link" href={value.link} target="_blank" rel="noreferrer">
                    <span class="card_source ">
                      {get_url_domain(value.link)}
                    </span>
                    <span class="card_date">
                      {value.date}
                    </span>
                    <h2 class="card_title">
                      {value.title}
                    </h2>
                    <h3 class="card_company">
                      {value.company}
                    </h3>
                  </a>
              </div>
            )
        })}
       
      </div>
    </div>
  );
}

export default withRouter(Offers);
