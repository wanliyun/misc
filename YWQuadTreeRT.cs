using System;
using System.Collections.Generic;
using UnityEngine;

class BuildContex<T>
{
	public float m_fMinRadius;//最小分割块的长度
	public Dictionary<TreeNodeRT<T>, List<T>> m_contex;
	public void AddObj(TreeNodeRT<T> node, T obj)
	{
		if (!m_contex.ContainsKey(node))
		{
			m_contex[node] = new List<T>();
		}
		m_contex[node].Add(obj);
	}
}
class TreeNodeRT<T>
{
	///	LB\RB\LT\RT
	static int[] ChildIdx2X = new int[] { -1, +1, -1, +1 };
	static int[] ChildIdx2Z = new int[] { -1, -1, +1, +1 };

	Vector3 m_vCenter;
	float m_fRadius;

	TreeNodeRT<T>[] m_children;
	T[] m_objArray;
	List<T> m_list = new List<T>();

	public TreeNodeRT(Vector3 center, float radius)
	{
		m_vCenter = center;
		m_fRadius = radius;
	}

	public void SetObjs(T[] arr)
	{
		m_objArray = arr;
	}

	bool isInChildRange(Vector3 objCenter, float objRadius, int childX, int childZ, ref Vector3 childCenter)
	{
		var cRadius = m_fRadius / 2;
		var cX = m_vCenter.x + cRadius * childX;
		var cZ = m_vCenter.z + cRadius * childZ;
		if( objCenter.x + objRadius < cX + cRadius &&
			objCenter.x - objRadius > cX - cRadius &&
			objCenter.z + objRadius < cZ + cRadius &&
			objCenter.z - objRadius > cZ - cRadius)
		{
			childCenter.x = cX;
			childCenter.z = cZ;
			return true;
		}
		return false;
	}

	bool isOverlap(Vector3 objCenter, float objRadius)
	{
		return Mathf.Abs(m_vCenter.x - objCenter.x) < m_fRadius + objRadius && Mathf.Abs(m_vCenter.z - objCenter.z) < m_fRadius + objRadius;
	}

	void insertIntoChild(int childIdx, Vector3 childCenter, BuildContex<T> buildCtx, Vector3 objCenter, float objRadius, T obj)
	{
		if (m_children == null)
			m_children = new TreeNodeRT<T>[4];
		if (m_children[childIdx] == null)
			m_children[childIdx] = new TreeNodeRT<T>(childCenter, m_fRadius / 2);
		m_children[childIdx].Insert(buildCtx, objCenter, objRadius, obj);
	}
	public void Insert(BuildContex<T> buildCtx, Vector3 objCenter, float objRadius, T obj)
	{
		bool isLeaf = m_fRadius < buildCtx.m_fMinRadius;
		if(isLeaf)
		{
			buildCtx.AddObj(this, obj);
		}
		int nearestChildIdx = -1;
		Vector3 nearestChildCenter = new Vector3();
		Vector3 childCenter = new Vector3();
		float minDist = 1e20f;
		for (int i = 0; i < 4; ++i)
		{
			if (isInChildRange(objCenter, objRadius, ChildIdx2X[i], ChildIdx2Z[i], ref childCenter))
			{
				insertIntoChild(i, childCenter, buildCtx, objCenter, objRadius, obj);
				return;
			}
			var sqrDist = (objCenter.x - childCenter.x) * (objCenter.x - childCenter.x) + (objCenter.z - childCenter.z) * (objCenter.z - childCenter.z);
			if (sqrDist < minDist)
			{
				nearestChildIdx = i;
				minDist = sqrDist;
				nearestChildCenter.x = objCenter.x;
				nearestChildCenter.y = objCenter.y;
				nearestChildCenter.z = objCenter.z;
			}
		}
		if (nearestChildIdx >= 0 && objRadius < m_fRadius)
		{
			insertIntoChild(nearestChildIdx, nearestChildCenter, buildCtx, objCenter, objRadius, obj);
			return;
		}
		buildCtx.AddObj(this, obj);
	}

	public void Query(Vector3 center, float radius, List<T> list)
	{
		if (!isOverlap(center, radius))
			return;
		if (m_objArray != null)
			list.AddRange(m_objArray);

		if (m_children != null)
		{
			for (int i = 0; i < 4; ++i)
			{
				if (m_children[i] != null)
					m_children[i].Query(center, radius, list);
			}
		}
	}
}

public class QuadTreeRT<T>
{
	TreeNodeRT<T> m_nodeRoot;
	BuildContex<T> m_buildCtx;

	public QuadTreeRT(Vector3 center, float range)
	{
		m_nodeRoot = new TreeNodeRT<T>(center, range);
	}

	public void StartBuild(float minRadius)
	{
		m_buildCtx = new BuildContex<T>();
		m_buildCtx.m_fMinRadius = minRadius;
		m_buildCtx.m_contex = new Dictionary<TreeNodeRT<T>, List<T>>();
	}
	public void Insert(Vector3 objCenter, float objRadius, T obj)
	{
		m_nodeRoot.Insert(m_buildCtx, objCenter, objRadius, obj);
	}
	public void FinishBuild()
	{
		foreach( var node in m_buildCtx.m_contex.Keys)
		{
			var lst = m_buildCtx.m_contex[node];
			node.SetObjs(lst.ToArray());
		}
		m_buildCtx = null;
	}

	public void Query(Vector3 center, float radius, List<T> list)
	{
		m_nodeRoot.Query(center, radius, list);
	}
}
