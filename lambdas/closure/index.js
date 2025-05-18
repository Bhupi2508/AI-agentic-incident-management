exports.handler = async (event) => {
  console.log("Closing incident", event);
  return { status: "closed", incidentId: event.incidentId };
};