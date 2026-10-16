"""Transactional local team ledger. Exercise contexts never borrow live resources."""
from contextlib import contextmanager
import json
from pathlib import Path
import secrets
import sqlite3
import uuid

from fastapi import HTTPException
from engine.config import ROOT

ACTIVE = ('assigned', 'accepted', 'en_route', 'arrived', 'blocked')
TRANSITIONS = {
    'assigned': {'accepted', 'cancelled'}, 'accepted': {'en_route', 'blocked', 'cancelled'},
    'en_route': {'arrived', 'blocked'}, 'arrived': {'completed', 'blocked'},
    'blocked': {'en_route'}, 'completed': set(), 'cancelled': set(),
}


class TeamStore:
    def __init__(self, path: Path | None = None):
        self.path = path or ROOT / 'data/runtime/operations.sqlite3'

    @contextmanager
    def transaction(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        try:
            db.executescript('''
              CREATE TABLE IF NOT EXISTS contexts(id TEXT PRIMARY KEY, source TEXT NOT NULL, label TEXT NOT NULL);
              CREATE TABLE IF NOT EXISTS teams(
                id TEXT PRIMARY KEY, context TEXT NOT NULL, name TEXT NOT NULL COLLATE NOCASE,
                location TEXT NOT NULL, members INTEGER NOT NULL, capabilities TEXT NOT NULL,
                available INTEGER NOT NULL, token TEXT NOT NULL UNIQUE, UNIQUE(context,name));
              CREATE TABLE IF NOT EXISTS assignments(
                id TEXT PRIMARY KEY, context TEXT NOT NULL, team_id TEXT NOT NULL, settlement_id TEXT NOT NULL,
                task TEXT NOT NULL, requirement TEXT NOT NULL, status TEXT NOT NULL,
                version INTEGER NOT NULL, source TEXT NOT NULL, event_time TEXT NOT NULL,
                recorded_at TEXT NOT NULL, evidence TEXT NOT NULL, request_id TEXT NOT NULL,
                UNIQUE(context,request_id));
              CREATE UNIQUE INDEX IF NOT EXISTS one_active_assignment ON assignments(team_id)
                WHERE status IN ('assigned','accepted','en_route','arrived','blocked');
              CREATE TABLE IF NOT EXISTS team_events(
                id INTEGER PRIMARY KEY AUTOINCREMENT, assignment_id TEXT NOT NULL,
                status TEXT NOT NULL, note TEXT NOT NULL, actor TEXT NOT NULL,
                event_time TEXT NOT NULL, recorded_at TEXT NOT NULL, request_id TEXT NOT NULL,
                UNIQUE(assignment_id,request_id));
            ''')
            db.execute('BEGIN IMMEDIATE')
            yield db
            db.commit()
        except sqlite3.IntegrityError as exc:
            db.rollback()
            raise HTTPException(409, 'Duplicate team name, request, or an existing active assignment. Refresh and try again.') from exc
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def remember(self, db, context):
        db.execute('INSERT OR IGNORE INTO contexts VALUES(?,?,?)', (context['id'], context['source'], context['label']))

    @staticmethod
    def team(row):
        result = dict(row)
        result['capabilities'] = json.loads(result['capabilities'])
        result['available'] = bool(result['available'])
        return result

    @staticmethod
    def assignment(db, row):
        result = dict(row)
        result['evidence'] = json.loads(result['evidence'])
        result['events'] = [dict(e) for e in db.execute('SELECT * FROM team_events WHERE assignment_id=? ORDER BY id', (row['id'],))]
        result['route_status'] = 'unverified'
        result['eta_minutes'] = None
        return result

    def list(self, context):
        with self.transaction() as db:
            teams = [self.team(r) for r in db.execute('SELECT * FROM teams WHERE context=? ORDER BY name', (context,))]
            tasks = [self.assignment(db,r) for r in db.execute('SELECT * FROM assignments WHERE context=? ORDER BY rowid DESC', (context,))]
            meta = db.execute('SELECT * FROM contexts WHERE id=?', (context,)).fetchone()
        return {'teams':teams, 'assignments':tasks, 'stored_context':dict(meta) if meta else None}

    def save_team(self, context, payload, ident=None):
        with self.transaction() as db:
            self.remember(db, context)
            if ident:
                existing = db.execute('SELECT * FROM teams WHERE id=? AND context=?', (ident,context['id'])).fetchone()
                if not existing: raise HTTPException(404, 'Team not found in this context')
                if db.execute("SELECT 1 FROM assignments WHERE team_id=? AND status IN ('assigned','accepted','en_route','arrived','blocked')", (ident,)).fetchone():
                    raise HTTPException(409, 'Team has an active commitment. Finish the task before changing its roster or availability.')
                db.execute('UPDATE teams SET name=?,location=?,members=?,capabilities=?,available=? WHERE id=?',
                           (payload.name,payload.location,payload.members,json.dumps(payload.capabilities),payload.available,ident))
            else:
                ident = uuid.uuid4().hex
                db.execute('INSERT INTO teams VALUES(?,?,?,?,?,?,?,?)',
                    (ident,context['id'],payload.name,payload.location,payload.members,json.dumps(payload.capabilities),payload.available,secrets.token_urlsafe(24)))
            return self.team(db.execute('SELECT * FROM teams WHERE id=?',(ident,)).fetchone())

    def dispatch(self, context, payload, evidence):
        with self.transaction() as db:
            self.remember(db,context)
            prior = db.execute('SELECT * FROM assignments WHERE context=? AND request_id=?',(context['id'],payload.request_id)).fetchone()
            if prior:
                if (prior['team_id'],prior['settlement_id'],prior['task'],prior['requirement']) != (payload.team_id,payload.settlement_id,payload.task,payload.requirement):
                    raise HTTPException(409,'Request ID was already used for a different assignment')
                return self.assignment(db,prior)
            team = db.execute('SELECT * FROM teams WHERE id=? AND context=?',(payload.team_id,context['id'])).fetchone()
            if not team: raise HTTPException(404,'Team not found in this context')
            if not team['available']: raise HTTPException(409,'Team is unavailable')
            if payload.requirement not in json.loads(team['capabilities']):
                raise HTTPException(409,'Team lacks the required capability')
            ident = uuid.uuid4().hex
            db.execute('INSERT INTO assignments VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',
                (ident,context['id'],payload.team_id,payload.settlement_id,payload.task,payload.requirement,
                 'assigned',1,context['source'],context['event_time'],context['recorded_at'],json.dumps(evidence),payload.request_id))
            db.execute('INSERT INTO team_events(assignment_id,status,note,actor,event_time,recorded_at,request_id) VALUES(?,?,?,?,?,?,?)',
                (ident,'assigned','Operator dispatched this task. Route/ETA unverified.','admin',context['event_time'],context['recorded_at'],payload.request_id))
            return self.assignment(db,db.execute('SELECT * FROM assignments WHERE id=?',(ident,)).fetchone())

    def portal(self, token):
        with self.transaction() as db:
            row = db.execute('SELECT * FROM teams WHERE token=?',(token,)).fetchone()
            if not row: raise HTTPException(404,'Unknown team link')
            team = self.team(row)
            tasks = [self.assignment(db,r) for r in db.execute('SELECT * FROM assignments WHERE team_id=? ORDER BY rowid DESC',(team['id'],))]
            context = dict(db.execute('SELECT * FROM contexts WHERE id=?',(team['context'],)).fetchone())
            return {'team':team,'assignments':tasks,'context':context}

    def update(self, context, ident, payload, *, team_id=None, admin=False):
        with self.transaction() as db:
            row = db.execute('SELECT * FROM assignments WHERE id=? AND context=?',(ident,context['id'])).fetchone()
            if not row or (not admin and row['team_id'] != team_id): raise HTTPException(404,'Assignment not found')
            prior = db.execute('SELECT * FROM team_events WHERE assignment_id=? AND request_id=?',(ident,payload.request_id)).fetchone()
            if prior:
                if prior['note'] != payload.note or (payload.status and prior['status'] != payload.status):
                    raise HTTPException(409,'Update ID already used for different content')
                return self.assignment(db,row)
            if row['version'] != payload.version: raise HTTPException(409,'Assignment changed. Refresh before updating.')
            status = payload.status or row['status']
            if admin and status != 'cancelled': raise HTTPException(403,'Admin action is limited to cancelling uncommitted work')
            if not admin and status == 'cancelled': raise HTTPException(403,'Only the control center can cancel a task')
            if row['status'] not in ACTIVE: raise HTTPException(409,'Task is finished; history is read-only')
            if status != row['status'] and status not in TRANSITIONS[row['status']]:
                raise HTTPException(409,f"Cannot move from {row['status']} to {status}")
            if status == row['status'] and not payload.note: raise HTTPException(422,'Enter a status note')
            if status == 'blocked' and not payload.note: raise HTTPException(422,'Describe the blockage and location')
            db.execute('UPDATE assignments SET status=?,version=version+1 WHERE id=?',(status,ident))
            if status in ('arrived','completed'):
                db.execute('UPDATE teams SET location=? WHERE id=?',(row['settlement_id'],row['team_id']))
            db.execute('INSERT INTO team_events(assignment_id,status,note,actor,event_time,recorded_at,request_id) VALUES(?,?,?,?,?,?,?)',
                (ident,status,payload.note,'admin' if admin else 'team',context['event_time'],context['recorded_at'],payload.request_id))
            return self.assignment(db,db.execute('SELECT * FROM assignments WHERE id=?',(ident,)).fetchone())
