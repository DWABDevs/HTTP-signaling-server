from sqlmodel import SQLModel, Field, create_engine, Session, ForeignKey, Relationship, select
from fastapi import FastAPI, Depends, HTTPException, Response, Request
from typing import List, Optional

# Define database connection
DATABASE_URL = "sqlite:///peers.db"



class Lobby(SQLModel, table=True):
    __tablename__ = "lobbies"
    id: int = Field(default=None, primary_key=True)
    name: str = Field(nullable=False)
    password: Optional[str] = Field(nullable=True)
    host_id:int = Field(foreign_key="peers.id", nullable=False)





# Define Peers table
class Peer(SQLModel, table=True):
    __tablename__ = "peers"
    id: int = Field(default=None, primary_key=True)
    name: str
    lobby_id:int = Field(foreign_key="lobbies.id", nullable=True)



class PeerConnection(SQLModel, table=True):
    __tablename__="peer_connections"
    id: int = Field(default=None, primary_key=True)
    source_peer_id:int = Field(foreign_key="peers.id", nullable=False)
    target_peer_id:int = Field(foreign_key="peers.id", nullable=False)
    lobby_id:int = Field(foreign_key="lobbies.id", nullable=False)
    sdp: str = Field(nullable=False)
    sdp_type: int = Field(nullable=False)

class ICECandidate(SQLModel, table=True):
    __tablename__="ice_candidates"
    id: int = Field(default=None, primary_key=True)
    candidate: str = Field(nullable=False)
    sdp_mid: str = Field(nullable=False)
    sdp_m_line_index: Optional[int]
    connection_id: int = Field(foreign_key="peer_connections.id", nullable=False)


class LobbyCreateInfo(SQLModel):
    name: str
    host_id: int
    password: str | None

class LobbyJoinInfo(SQLModel):
    lobby_id: int
    peer_id: int
    password: str | None


engine = create_engine(DATABASE_URL, echo=False)
SQLModel.metadata.create_all(engine)

# Create a session
def get_db():
    with Session(engine) as session:
        yield session

app = FastAPI()


@app.get("/")
def default():
    return "This is a http signaling server made for peer to peer connections for dwab games"


@app.post("/register")
def register(peerInfo: Peer, db: Session = Depends(get_db)):
    new_peer= Peer(name=peerInfo.name, lobby_id=None)
    db.add(new_peer)
    db.commit()
    db.refresh(new_peer)
    return new_peer


@app.post("/create-lobby")
def register(lobby_create_info: LobbyCreateInfo, db: Session = Depends(get_db)):
    new_lobby = Lobby(name=lobby_create_info.name, host_id=lobby_create_info.host_id, password=lobby_create_info.password)
    db.add(new_lobby)
    db.commit()
    db.refresh(new_lobby)
    return new_lobby

@app.get("/lobbies")
def get_lobbies( db: Session = Depends(get_db)):
    statement = select(Lobby).order_by(Lobby.id.desc())
    lobbies = db.exec(statement)
    return lobbies.all()
    


@app.post("/join-lobby")
def register(lobby_join_info: LobbyJoinInfo, db: Session = Depends(get_db)):
    statement = select(Lobby).where(Lobby.id == lobby_join_info.lobby_id)
    try:
        lobbies = db.exec(statement=statement)
        lobby = lobbies.one()
        peer = db.exec(select(Peer).where(Peer.id == lobby_join_info.peer_id)).one()
        peer.lobby_id = lobby.id
        db.add(peer)
        db.commit()
        db.refresh(peer)
        db.refresh(lobby)
        return lobby
    except Exception:
        raise HTTPException(404)


@app.get("/peers/{peer_id}")
def register(peer_id:int, db: Session = Depends(get_db)):
    return db.exec(select(Peer).where(Peer.id == peer_id)).one()

@app.post("/create-connection")
def create_connection(connection: PeerConnection, db: Session = Depends(get_db)):
    connection.id = None
    db.add(connection)
    db.commit()
    db.refresh(connection)
    return connection

@app.post("/ice-candidate")
def post_candidate(candidate: ICECandidate, db: Session = Depends(get_db)):
    candidate.id = None
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    return candidate





@app.get("/poll-connections/{peer_id}")
def poll_offers(peer_id: int,  db: Session = Depends(get_db)):
    return db.exec(select(PeerConnection).where(PeerConnection.target_peer_id == peer_id)).all()
    
@app.get("/poll-candidates/{connection_id}")
def poll_offers(connection_id: int,  db: Session = Depends(get_db)):
    return db.exec(select(ICECandidate).where(ICECandidate.connection_id == connection_id)).all()
    




