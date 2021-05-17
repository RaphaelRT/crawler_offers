import 'font-awesome/css/font-awesome.min.css';
import './index.css'
import Offers from "./Offers"
import React from 'react';

import {
  BrowserRouter as Router,
  Switch,
  Route
} from "react-router-dom";

export default function App() {
  console.log(process.env)
  return (
    <Router>
      <Switch>
        <Route path="/" children={<Offers />} />
        <Route path="/fav" children={<Offers />} />
      </Switch>
    </Router>
  ); 
}